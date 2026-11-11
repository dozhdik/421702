"""Local WSGI presentation for the corporate blog."""

from __future__ import annotations

import html
import re
import sqlite3
import time
from pathlib import Path
from email.parser import BytesParser
from email.policy import default
from typing import Any, Callable
from urllib.parse import parse_qs, quote

from omis_blog import domain as d
from omis_blog.auth import authenticate, has_permission, register_author, role
from omis_blog.localization import status_label, error_message, role_label


def escape_html(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def render_markdown(value: str) -> str:
    """Render a small safe subset of Markdown after escaping user input."""
    blocks = []
    paragraph: list[str] = []
    def flush() -> None:
        if paragraph:
            blocks.append("<p>" + "<br>".join(paragraph) + "</p>")
            paragraph.clear()
    for line in value.splitlines():
        line = line.strip()
        if not line:
            flush()
        elif line.startswith("### "):
            flush()
            blocks.append("<h3>" + escape_html(line[4:]) + "</h3>")
        elif line.startswith("## "):
            flush()
            blocks.append("<h2>" + escape_html(line[3:]) + "</h2>")
        elif line.startswith("# "):
            flush()
            blocks.append("<h2>" + escape_html(line[2:]) + "</h2>")
        else:
            paragraph.append(escape_html(line))
    flush()
    return "".join(blocks)


def form_data(environ: dict) -> tuple[dict[str, str], list[tuple[str, bytes, str]]]:
    length = min(int(environ.get("CONTENT_LENGTH") or 0), 6_000_000)
    raw = environ["wsgi.input"].read(length)
    content_type = environ.get("CONTENT_TYPE", "")
    if content_type.startswith("multipart/form-data"):
        parsed = BytesParser(policy=default).parsebytes(
            b"Content-Type: " + content_type.encode() + b"\r\nMIME-Version: 1.0\r\n\r\n" + raw)
        data: dict[str, str] = {}
        files: list[tuple[str, bytes, str]] = []
        for part in parsed.iter_parts():
            raw_name = part.get_param("name", header="content-disposition")
            name = raw_name if isinstance(raw_name, str) else ""
            filename = part.get_filename()
            raw_payload = part.get_payload(decode=True)
            payload = raw_payload if isinstance(raw_payload, bytes) else b""
            if isinstance(filename, str) and filename:
                files.append((filename, payload, part.get_content_type()))
            else:
                data[name] = payload.decode("utf-8", "replace")
        return data, files
    return {k: v[0] for k, v in parse_qs(raw.decode("utf-8"), keep_blank_values=True).items()}, []


class WebApp:
    def __init__(self, app: Any) -> None:
        self.app = app
        self.db = app.db
        self.publications, self.moderation, self.notices, self.feed, self.reports = app.controllers
        self.session: d.UserSession | None = None
        self.account: d.UserAccount | None = None
        self.cookie = ""
        self.params: dict[str, str] = {}
        self.current_path = "/"
        self.ui_states: dict[str, d.InterfaceSubsystem] = {}
        self.ui = d.InterfaceSubsystem()
        self.secure_cookie = False
        self.login_attempts: dict[str, list[float]] = {}

    def __call__(self, environ: dict, start_response: Callable) -> list[bytes]:
        path = environ.get("PATH_INFO", "/")
        self.current_path = path
        method = environ.get("REQUEST_METHOD", "GET")
        self.params = {k: v[0] for k, v in parse_qs(environ.get("QUERY_STRING", "")).items()}
        self.cookie = ""
        self.secure_cookie = environ.get("wsgi.url_scheme") == "https"
        self._session(environ)
        body: str | bytes
        try:
            if method == "POST":
                data, files = form_data(environ)
                if not self.session or data.get("csrf") != self.session.authorization_token:
                    raise d.PermissionDenied("Неверный токен формы")
                status, body, headers = self._post(path, data, files)
            else:
                status, body, headers = self._get(path)
        except d.PermissionDenied as exc:
            status, body, headers = "403 Forbidden", self._page("Нет доступа", f'<p role="alert">{escape_html(error_message(str(exc)))}</p>'), []
        except d.NotFound as exc:
            status, body, headers = "404 Not Found", self._page("Не найдено", f"<p>{escape_html(exc)}</p>"), []
        except (d.DomainException, sqlite3.IntegrityError, ValueError) as exc:
            status, body, headers = "400 Bad Request", self._page("Ошибка", f'<p role="alert">{escape_html(error_message(str(exc)))}</p>'), []
        if self.cookie:
            headers.append(("Set-Cookie", self.cookie))
        if not any(k.lower() == "content-type" for k, _ in headers):
            headers.append(("Content-Type", "text/html; charset=utf-8"))
        start_response(status, headers)
        return [body if isinstance(body, bytes) else body.encode("utf-8")]

    def _session(self, environ: dict) -> None:
        cookie = environ.get("HTTP_COOKIE", "")
        found = re.search(r"(?:^|;\s*)sid=([a-f0-9-]{36})", cookie)
        self.session = self.db.get(d.UserSession, found.group(1)) if found else None
        self.account = None
        if self.session and self.session.user_id:
            accounts = self.db.list_entities(d.UserAccount, 'user_id=?',
                                      (self.session.user_id,))
            self.account = accounts[0] if accounts and accounts[0].is_active else None
        if self.session is None:
            self.session = d.UserSession()
            self.db.save(self.session)
            self.cookie = self._cookie(self.session.session_id)
        if self.session.session_id not in self.ui_states:
            self.ui_states[self.session.session_id] = d.InterfaceSubsystem(
                connection_status="connected", feed=d.PublicationFeed(),
                form=d.ArticleEditorFormState(), dashboard=d.ModeratorDashboardState(),
                viewer=d.ArticleViewerState())
        self.ui = self.ui_states[self.session.session_id]
        for view, state in zip(self.app.views,
                               (self.ui.feed, self.ui.form, self.ui.dashboard, self.ui.viewer)):
            view.state = state
        if self.session not in self.ui.sessions:
            self.ui.sessions.append(self.session)
        self.ui.logged_in_at = self.session.logged_in_at

    def _cookie(self, session_id: str) -> str:
        return f"sid={session_id}; HttpOnly; SameSite=Lax; Path=/" + ("; Secure" if self.secure_cookie else "")

    def _rotate_session(self, user_id: str) -> None:
        assert self.session
        old_id = self.session.session_id
        self.db.delete(d.UserSession, old_id)
        self.ui_states.pop(old_id, None)
        self.session = d.UserSession(user_id=user_id)
        self.db.save(self.session)
        self.cookie = self._cookie(self.session.session_id)
        self.account = self.db.list_entities(d.UserAccount, 'user_id=?', (user_id,))[0]

    def _require(self, operation: str) -> None:
        if not has_permission(self.db, self.account, operation):
            raise d.PermissionDenied(operation)

    def _csrf(self) -> str:
        assert self.session
        return f'<input type="hidden" name="csrf" value="{escape_html(self.session.authorization_token)}">'

    def _navigation_link(self, label: str, target: str, class_name: str = "") -> str:
        active = self.current_path == target or (
            target != "/" and self.current_path.startswith(target + "/")
        )
        classes = f' class="{class_name}"' if class_name else ""
        current = ' aria-current="page"' if active else ""
        return f'<a href="{target}"{classes}{current}>{escape_html(label)}</a>'

    def _header(self) -> str:
        nav = [self._navigation_link("Статьи", "/")]
        if self.account:
            if has_permission(self.db, self.account, "article.write"):
                nav.append(self._navigation_link("Мои статьи", "/my-articles"))
            if has_permission(self.db, self.account, "article.moderate"):
                nav.append(self._navigation_link("Модерация", "/moderation"))
            if has_permission(self.db, self.account, "admin"):
                nav.append(self._navigation_link("Администрирование", "/admin"))
            unread_count = self.db.connection.execute(
                "SELECT COUNT(*) FROM notification WHERE recipient=? AND is_read=0",
                (self.account.user_id,)).fetchone()[0]
            notification_label = "Уведомления"
            if unread_count:
                notification_label += f" ({unread_count})"
            nav.append(self._navigation_link(notification_label, "/notifications"))
            account = self.db.get(d.User, self.account.user_id)
            account_label = account.full_name if account else self.account.login
            account_actions = (
                f'<span class="account-label">{escape_html(account_label)}</span>'
                f'<form method="post" action="/logout" class="logout-form">{self._csrf()}'
                '<button class="button button-quiet" type="submit">Выйти</button></form>'
            )
        else:
            account_actions = (self._navigation_link("Войти", "/login", "button button-quiet")
                               + self._navigation_link("Регистрация", "/register", "button button-primary"))
        writing_action = ""
        if has_permission(self.db, self.account, "article.write"):
            writing_action = self._navigation_link("Написать статью", "/editor/new", "button button-primary")
        return (
            '<header class="site-header"><div class="header-inner">'
            '<a class="brand" href="/" aria-label="Корпоративный блог — главная">'
            '<span class="brand-mark" aria-hidden="true">✦</span><span>Корпоративный блог</span></a>'
            f'<nav class="primary-navigation" aria-label="Основная навигация">{"".join(nav)}</nav>'
            f'<div class="header-actions">{writing_action}{account_actions}</div>'
            '</div></header>'
        )

    def _page(self, title: str, body: str, subtitle: str = "") -> str:
        role_name = role(self.db, self.account)
        role_display = f'<p class="role-label">{escape_html(role_label(role_name))}</p>' if role_name else ""
        subtitle_html = f'<p class="page-subtitle">{escape_html(subtitle)}</p>' if subtitle else ""
        return (
            '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape_html(title)} · Корпоративный блог</title>'
            '<link rel="stylesheet" href="/assets/site.css"></head><body>'
            f'{self._header()}<main class="site-main"><header class="page-heading">'
            f'<h1>{escape_html(title)}</h1>{subtitle_html}{role_display}</header>'
            f'<div class="page-content">{body}</div></main>'
            '<footer class="site-footer"><div class="footer-inner">'
            '<span>Корпоративный блог</span><span>Идеи, новости и опыт нашей команды</span>'
            '</div></footer></body></html>'
        )

    @staticmethod
    def _redirect(path: str) -> tuple[str, str, list[tuple[str, str]]]:
        return "303 See Other", "", [("Location", path)]

    def _get(self, path: str) -> tuple[str, str | bytes, list[tuple[str, str]]]:
        if path == "/assets/site.css":
            return "200 OK", Path(__file__).with_name("site.css").read_bytes(), [("Content-Type", "text/css; charset=utf-8")]
        if path == "/login":
            body = f'<form class="auth-form" method="post" action="/login">{self._csrf()}<label>Логин <input name="login" autocomplete="username" required></label><label>Пароль <input type="password" name="password" autocomplete="current-password" required></label><button class="primary">Войти</button><p>Нет учётной записи? <a href="/register">Зарегистрироваться</a></p></form>'
            return "200 OK", self._page("Вход", body), []
        if path == "/register":
            body = (f'<form class="auth-form" method="post" action="/register">{self._csrf()}'
                    '<label>ФИО <input name="full_name" maxlength="120" autocomplete="name" required></label>'
                    '<label>Логин <input name="login" minlength="3" maxlength="40" autocomplete="username" required></label>'
                    '<label>Пароль <input type="password" name="password" minlength="10" maxlength="128" autocomplete="new-password" required></label>'
                    '<label>Повторите пароль <input type="password" name="confirmation" minlength="10" maxlength="128" autocomplete="new-password" required></label>'
                    '<button class="primary">Создать аккаунт</button><p>Уже есть аккаунт? <a href="/login">Войти</a></p></form>')
            return "200 OK", self._page("Регистрация", body), []
        if path == "/":
            return "200 OK", self._page("Корпоративный блог", self._feed(),
                                        "Новости, идеи и опыт нашей команды"), []
        if path == "/my-articles":
            self._require("article.write")
            return "200 OK", self._page("Мои статьи", self._my_articles()), []
        if path.startswith("/article/"):
            return "200 OK", self._page("Статья", self._article(path.split("/")[2])), []
        if path.startswith("/editor/"):
            self._require("article.write")
            return "200 OK", self._page("Редактор статьи", self._editor(path.split("/")[2])), []
        if path == "/moderation":
            self._require("article.moderate")
            return "200 OK", self._page("Кабинет редактора", self._moderation()), []
        if path == "/admin":
            self._require("admin")
            return "200 OK", self._page("Администрирование", self._admin()), []
        if path == "/notifications":
            if not self.account:
                raise d.PermissionDenied("Войдите")
            body = "".join(f'<article>{escape_html(row["text"])} <small>{escape_html(row["created_at"])}</small></article>'
                           for row in self.notices.inbox(self.account.user_id))
            return "200 OK", self._page("Уведомления", body or "<p>Пока нет уведомлений.</p>"), []
        if path.startswith("/media/"):
            return self._media(path.split("/")[2])
        raise d.NotFound(path)

    def _feed(self) -> str:
        page = max(1, int(self.params.get("page", "1")))
        query = self.params.get("q", "")
        author = self.params.get("author", "")
        rubric = self.params.get("rubric", "")
        tag = self.params.get("tag", "")
        articles = self.feed.search(query, author, rubric, tag, page, 10)
        view = self.app.views[0]
        view.state.current_page = page
        view.state.selected_filter = rubric
        view.display_feed(articles)
        self.ui.feed_updated_at = d.utc_now()
        if rubric:
            self.ui.filter_applied_at = d.utc_now()
        options = '<option value="">Все рубрики</option>' + "".join(
            f'<option value="{escape_html(r.category_id)}" {"selected" if r.category_id == rubric else ""}>{escape_html(r.name)}</option>'
            for r in self.db.list_entities(d.Category))
        body = (f'<form class="search-panel" method="get" role="search">'
                '<label>Поиск по статьям<input name="q" type="search" placeholder="Тема или слово" '
                f'value="{escape_html(query)}"></label>'
                '<label>Автор<input name="author" placeholder="Имя автора" '
                f'value="{escape_html(author)}"></label>'
                '<label>Тег<input name="tag" placeholder="Например, команда" '
                f'value="{escape_html(tag)}"></label>'
                f'<label>Рубрика<select name="rubric">{options}</select></label>'
                '<button class="button button-primary" type="submit">Найти</button></form>')
        if articles:
            body += self._article_card(articles[0], featured=True)
            remaining_articles = articles[1:]
            if remaining_articles:
                body += '<section class="feed-section" aria-labelledby="feed-list-heading">'
                body += '<h2 id="feed-list-heading" class="section-heading">Свежие публикации</h2>'
                body += '<div class="article-grid">'
                body += "".join(self._article_card(article) for article in remaining_articles)
                body += '</div></section>'
        if not articles:
            body += ('<section class="empty-state" aria-live="polite"><h2>По этому запросу пока ничего нет</h2>'
                     '<p>Измените слова поиска или выберите другую рубрику.</p>'
                     '<a class="button button-secondary" href="/">Сбросить фильтры</a></section>')
        if page > 1:
            body += (f'<a class="pagination-link" href="?page={page-1}&q={quote(query)}&author={quote(author)}'
                     f'&rubric={quote(rubric)}&tag={quote(tag)}">Назад</a> ')
        if len(articles) == 10:
            body += (f'<a class="pagination-link" href="?page={page+1}&q={quote(query)}&author={quote(author)}'
                     f'&rubric={quote(rubric)}&tag={quote(tag)}">Следующая страница</a>')
        return body

    def _article_card(self, article: d.Article, featured: bool = False) -> str:
        author = self.db.get(d.ContentAuthor, article.author_id)
        category = self.db.get(d.Category, article.category_id)
        category_name = category.name if category else "Блог"
        options = self.db.list_entities(d.FormattingOptions, 'article_id=?', (article.article_id,))
        show_preview = options[0].has_preview if options else True
        reactions = len(self.db.list_entities(d.Reaction, 'article_id=?', (article.article_id,)))
        comments = len(self.db.list_entities(d.Comment, 'article_id=?', (article.article_id,)))
        preview_text = article.summary or re.sub(r"[#*]", "", article.content)[:220]
        read_minutes = max(1, round(len(article.content.split()) / 180))
        theme = article.cover_theme if article.cover_theme in ("indigo", "sky", "emerald", "amber", "rose") else "indigo"
        media = next((item for item in self.db.list_entities(
            d.MediaAttachment, 'article_id=?', (article.article_id,))
            if item.content_type.startswith("image/")), None)
        cover = (f'<img class="cover-image" src="/media/{escape_html(media.media_id)}" '
                 f'alt="Иллюстрация к статье: {escape_html(article.title)}">' if media else
                 f'<span class="cover-symbol" aria-hidden="true">✦</span>')
        date = article.published_at.date().isoformat() if article.published_at else ""
        read_label = f'{read_minutes} мин чтения'
        featured_class = " featured-card" if featured else ""
        return (
            f'<article class="article-card{featured_class}">'
            f'<a class="card-cover cover-{theme}" href="/article/{escape_html(article.article_id)}" '
            f'aria-label="Открыть статью: {escape_html(article.title)}">'
            f'<span class="cover-category">{escape_html(category_name)}</span>{cover}</a>'
            '<div class="card-content">'
            f'<p class="eyebrow">{escape_html(category_name)}</p>'
            f'<h2><a href="/article/{escape_html(article.article_id)}">{escape_html(article.title)}</a></h2>'
            + (f'<p class="article-excerpt">{escape_html(preview_text)}</p>' if show_preview else '')
            + f'<p class="card-meta">{escape_html(author.full_name if author else "")} · {escape_html(date)} · {read_label}</p>'
            + f'<p class="card-counts"><span>{reactions} реакций</span><span>{comments} комментариев</span></p>'
            + '</div></article>'
        )

    def _my_articles(self) -> str:
        author = self._profile(d.ContentAuthor)
        if author is None:
            raise d.PermissionDenied("author_profile_missing")
        selected = self.params.get("status", "all")
        statuses = [("all", "Все"), *[(item.value, status_label(item)) for item in d.ArticleStatus]]
        links = '<nav class="filter-nav" aria-label="Фильтр статей">' + "".join(
            f'<a class="{"selected" if selected == value else ""}" href="/my-articles?status={escape_html(value)}">{escape_html(label)}</a>'
            for value, label in statuses) + '</nav>'
        articles = self.db.list_entities(d.Article, 'author_id=? AND deleted_at IS NULL',
                                         (author.author_id,), 'created_at DESC')
        if selected != "all":
            articles = [item for item in articles if item.publication_status.value == selected]
        body = links + '<div class="my-articles">'
        for item in articles:
            editable = item.publication_status in (d.ArticleStatus.DRAFT, d.ArticleStatus.NEEDS_REVISION)
            href = f'/editor/{escape_html(item.article_id)}' if editable else f'/article/{escape_html(item.article_id)}'
            body += (f'<article class="list-card"><span class="status-badge">{escape_html(status_label(item.publication_status))}</span>'
                     f'<h2><a href="{href}">{escape_html(item.title or "Без названия")}</a></h2>'
                     f'<p class="muted">Создано {escape_html(item.created_at.date())}</p>')
            for note in self.db.list_entities(d.EditorRemark, 'article_id=?', (item.article_id,)):
                body += f'<p class="editor-note"><strong>Замечание редактора:</strong> {escape_html(note.remark_text)}</p>'
            body += self._delete_form(item.article_id)
            body += '</article>'
        return body + ('</div>' if articles else '<p class="empty-state">Статей пока нет. <a href="/editor/new">Напишите первую статью</a>.</p></div>')

    def _can_delete_article(self, article: d.Article) -> bool:
        author = self._profile(d.ContentAuthor)
        owns_article = bool(author and author.author_id == article.author_id)
        return bool(self.account and (
            owns_article and has_permission(self.db, self.account, "article.write")
            or has_permission(self.db, self.account, "article.delete.any")
        ))

    def _delete_form(self, article_id: str) -> str:
        return (f'<form class="article-delete-form" method="post" '
                f'action="/article/{escape_html(article_id)}/delete" '
                'onsubmit="return confirm(&quot;Удалить статью? Это действие нельзя отменить.&quot;)">'
                f'{self._csrf()}<button class="danger" type="submit">Удалить</button></form>')

    def _article(self, article_id: str) -> str:
        article = self.db.get(d.Article, article_id)
        if article is None or article.deleted_at is not None:
            raise d.NotFound(article_id)
        author = self._profile(d.ContentAuthor)
        if article.publication_status != d.ArticleStatus.PUBLISHED and not (
            author and author.author_id == article.author_id or has_permission(self.db, self.account, "article.moderate")
        ):
            raise d.PermissionDenied("Статья ещё не опубликована")
        if article.publication_status == d.ArticleStatus.PUBLISHED:
            article.view_count += 1
            self.db.save(article)
            self.db.connection.execute('INSERT INTO article_view VALUES (?, ?, ?)',
                                       (d.new_id(), article_id, d.utc_now().isoformat()))
            self.db.connection.commit()
        self.app.views[3].open_article(article_id)
        self.ui.article_opened_at = d.utc_now()
        styles = self.db.list_entities(d.FormattingOptions, 'article_id=?', (article_id,))
        font = "serif" if styles and styles[0].font == "serif" else "system-ui"
        category = self.db.get(d.Category, article.category_id)
        author_record = self.db.get(d.ContentAuthor, article.author_id)
        article_date = article.published_at.date().isoformat() if article.published_at else ""
        body = (f'<article class="article-reading"><p class="eyebrow">{escape_html(category.name if category else "Блог")}</p>'
                f'<h2 class="reading-title">{escape_html(article.title)}</h2>'
                f'<p class="article-summary">{escape_html(article.summary)}</p>'
                '<div class="article-byline">'
                f'<span>{escape_html(author_record.full_name if author_record else "Автор")}</span>'
                f'<time datetime="{escape_html(article.published_at.isoformat() if article.published_at else "")}">{escape_html(article_date)}</time>'
                '</div>'
                f'<div class="article-body font-{font}" style="font-family:{font}">{render_markdown(article.content)}</div>')
        if author and author.author_id == article.author_id or has_permission(self.db, self.account, "article.moderate"):
            body += f'<p class="muted">Статус: {escape_html(status_label(article.publication_status))} · просмотры: {article.view_count}</p>'
        body += '<p>Теги: ' + ', '.join(escape_html(tag.keyword) for tag in self.db.get_article_tags(article_id)) + '</p>'
        for media in self.db.list_entities(d.MediaAttachment, 'article_id=?', (article_id,)):
            if media.content_type.startswith("image/"):
                body += (f'<figure class="article-media"><img src="/media/{escape_html(media.media_id)}" '
                         f'alt="Иллюстрация к статье: {escape_html(article.title)}"></figure>')
            body += f'<p><a href="/media/{escape_html(media.media_id)}">Вложение: {escape_html(media.file_url)}</a></p>'
        if article.publication_status == d.ArticleStatus.PUBLISHED:
            reactions = self.db.list_entities(d.Reaction, 'article_id=?', (article_id,))
            comments = self.db.list_entities(d.Comment, 'article_id=?', (article_id,), 'added_at')
            visible_comments = [comment for comment in comments if comment.status == d.CommentStatus.VISIBLE]
            body += (f'<section class="article-engagement" aria-label="Обсуждение статьи">'
                     f'<span>{len(reactions)} реакций</span><span>{len(visible_comments)} комментариев</span></section>')
            if self.account:
                body += (f'<form method="post" action="/article/{escape_html(article_id)}/react">{self._csrf()}'
                         '<label>Ваша реакция<select name="type"><option value="like">Нравится</option>'
                         '<option value="helpful">Полезно</option></select></label>'
                         '<button class="button button-secondary" type="submit">Отметить</button></form>')
            self.app.views[3].display_comments(comments)
            body += f'<section class="comments-section"><h2>Обсуждение <span class="heading-count">{len(visible_comments)}</span></h2>'
            if not visible_comments:
                body += '<p class="empty-state">Пока нет комментариев. Начните обсуждение.</p>'
            for comment in comments:
                text = escape_html(comment.text) if comment.status == d.CommentStatus.VISIBLE else '[Комментарий скрыт]'
                reply_class = " comment-reply" if comment.parent_id else ""
                body += (f'<article class="comment-card{reply_class}" id="c-{escape_html(comment.comment_id)}">'
                         f'<p>{text}</p>')
                if comment.parent_id:
                    parent = self.db.get(d.Comment, comment.parent_id)
                    parent_label = (
                        parent.text[:72]
                        if parent and parent.status == d.CommentStatus.VISIBLE
                        else "скрытый комментарий"
                    )
                    body += f'<small class="reply-context">В ответ на: {escape_html(parent_label)}</small>'
                if self.account and comment.status == d.CommentStatus.VISIBLE:
                    body += (f'<form method="post" action="/article/{escape_html(article_id)}/comment">{self._csrf()}'
                             f'<input type="hidden" name="parent" value="{escape_html(comment.comment_id)}">'
                             '<label>Ответ<textarea name="text" required rows="2"></textarea></label>'
                             '<button class="button button-quiet" type="submit">Ответить</button></form>'
                             f'<form method="post" action="/article/{escape_html(article_id)}/report">{self._csrf()}'
                             f'<input type="hidden" name="comment" value="{escape_html(comment.comment_id)}">'
                             '<label>Причина жалобы<input name="reason" required></label>'
                             '<button class="button button-quiet" type="submit">Пожаловаться</button></form>')
                body += '</article>'
            if self.account:
                body += (f'<form method="post" action="/article/{escape_html(article_id)}/comment">{self._csrf()}'
                         '<label>Ваш комментарий<textarea name="text" required rows="4"></textarea></label>'
                         '<button class="button button-primary" type="submit">Отправить комментарий</button></form>')
            else:
                body += '<p class="login-prompt">Чтобы присоединиться к обсуждению, <a href="/login">войдите в аккаунт</a>.</p>'
            body += '</section>'
        if has_permission(self.db, self.account, "article.moderate") and article.publication_status in (
            d.ArticleStatus.PUBLISHED, d.ArticleStatus.ARCHIVED, d.ArticleStatus.UNPUBLISHED
        ):
            body += f'<form method="post" action="/article/{escape_html(article_id)}/status">{self._csrf()}'
            if article.publication_status == d.ArticleStatus.PUBLISHED:
                body += ('<button name="status" value="archived">В архив</button> '
                         '<button name="status" value="unpublished">Снять с публикации</button>')
            else:
                body += '<button name="status" value="published">Восстановить публикацию</button>'
            body += '</form>'
        if self._can_delete_article(article):
            body += self._delete_form(article_id)
        return body + '</article>'

    def _profile(self, cls: type) -> Any:
        if not self.account:
            return None
        profiles = self.db.list_entities(cls, 'user_id=?', (self.account.user_id,))
        return profiles[0] if profiles else None

    def _editor(self, article_id: str) -> str:
        author = self._profile(d.ContentAuthor)
        if author is None:
            raise d.PermissionDenied("Нет профиля автора")
        article = None if article_id == "new" else self.db.get(d.Article, article_id)
        if article_id != "new" and article is None:
            raise d.NotFound(article_id)
        if article and article.deleted_at is not None:
            raise d.NotFound(article_id)
        if article and (article.author_id != author.author_id or article.publication_status not in
                        (d.ArticleStatus.DRAFT, d.ArticleStatus.NEEDS_REVISION)):
            raise d.PermissionDenied("Редактировать можно только свой черновик")
        article = article or d.Article()
        rubric_options = '<option value="">Выберите рубрику</option>' + "".join(
            f'<option value="{escape_html(r.category_id)}" {"selected" if r.category_id == article.category_id else ""}>{escape_html(r.name)}</option>'
            for r in self.db.list_entities(d.Category))
        tags = ", ".join(t.keyword for t in self.db.get_article_tags(article.article_id)) if article_id != "new" else ""
        style = self.db.list_entities(d.FormattingOptions, 'article_id=?', (article.article_id,))
        font = style[0].font if style else "system"
        preview = style[0].has_preview if style else True
        body = (f'<form id="editor" method="post" action="/article/save" enctype="multipart/form-data">{self._csrf()}'
                f'<input type="hidden" name="id" value="{escape_html(article_id if article_id != "new" else "")}">'
                f'<label>Заголовок<input name="title" value="{escape_html(article.title)}"></label>'
                f'<label>Содержание<textarea name="content">{escape_html(article.content)}</textarea></label>'
                f'<label>Рубрика<select name="rubric">{rubric_options}</select></label>'
                f'<label>Теги через запятую<input name="tags" value="{escape_html(tags)}"></label>'
                f'<label>Шрифт<select name="font"><option value="system" {"selected" if font == "system" else ""}>Системный</option>'
                f'<option value="serif" {"selected" if font == "serif" else ""}>С засечками</option></select></label>'
                f'<label><input type="checkbox" name="preview" {"checked" if preview else ""}>Показывать превью</label>'
                '<label>Медиавложение (PNG, JPEG, PDF; до 5 МБ)<input type="file" name="media" accept="image/png,image/jpeg,application/pdf"></label>'
                '<button name="action" value="draft">Сохранить черновик</button> '
                '<button name="action" value="submit">Отправить на модерацию</button>'
                '<span id="autosave" class="muted">Не сохранено автоматически</span></form>')
        if article_id != "new":
            body += self._delete_form(article.article_id)
            for media in self.db.list_entities(d.MediaAttachment, 'article_id=?', (article.article_id,)):
                body += (f'<p><a href="/media/{escape_html(media.media_id)}">{escape_html(media.file_url)}</a> '
                         f'<form class="inline" method="post" action="/media/{escape_html(media.media_id)}/delete">'
                         f'{self._csrf()}<button>Удалить вложение</button></form></p>')
            for note in self.db.list_entities(d.EditorRemark, 'article_id=?', (article.article_id,)):
                body += f'<article><strong>Замечание редактора:</strong> {escape_html(note.remark_text)}</article>'
        body += ("<script>let dirty=false;const editorForm=document.querySelector('#editor');"
                 "editorForm.addEventListener('input',()=>dirty=true);"
                 "setInterval(async()=>{if(!dirty)return;const formData=new FormData(editorForm);formData.set('action','autosave');formData.delete('media');"
                 "try{const response=await fetch('/article/save',{method:'POST',body:formData});"
                 "document.querySelector('#autosave').textContent=response.ok?'Автосохранено':'Ошибка автосохранения';"
                 "if(response.ok){dirty=false;const articleId=response.headers.get('X-Article-ID');"
                 "if(articleId){editorForm.querySelector('[name=id]').value=articleId;history.replaceState(null,'','/editor/'+articleId);}}}"
                 "catch(error){document.querySelector('#autosave').textContent='Ошибка автосохранения';}},30000);</script>")
        self.app.views[1].display_draft(article.content)
        return body

    def _moderation(self) -> str:
        selected = self.params.get("filter", "all")
        self.app.views[2].display_queue(selected)
        body = ('<p><a href="/moderation?filter=all">Всё</a> · '
                '<a href="/moderation?filter=articles">Статьи</a> · '
                '<a href="/moderation?filter=complaints">Жалобы</a></p>')
        if selected in ("all", "articles"):
            tickets = self.db.list_entities(d.ModerationQueueEntry,
                                     'processed_at IS NULL AND article_id IN '
                                     '(SELECT article_id FROM Article WHERE deleted_at IS NULL)',
                                     order='priority DESC, received_at')
            body += '<h2>Статьи</h2>'
            if not tickets:
                body += '<p class="empty-state">Материалов на модерации нет.</p>'
            for ticket in tickets:
                article = self.db.get(d.Article, ticket.article_id)
                if article is None:
                    continue
                body += (f'<article><strong>{escape_html(article.title)}</strong> · приоритет {ticket.priority}'
                         f'<p>{escape_html(article.content)}</p><a href="/article/{escape_html(article.article_id)}">Открыть статью и вложения</a>'
                         f'<form method="post" action="/moderation/priority/{escape_html(ticket.queue_entry_id)}">{self._csrf()}'
                         f'<label>Приоритет <input type="number" min="0" max="10" name="priority" value="{ticket.priority}"></label>'
                         '<button>Установить приоритет</button></form>'
                         f'<form method="post" action="/moderation/article/{escape_html(article.article_id)}">{self._csrf()}'
                         '<label>Замечание<textarea name="note"></textarea></label>'
                         '<button name="decision" value="reject">Вернуть на доработку</button> '
                         '<button name="decision" value="approve">Одобрить и опубликовать</button></form></article>')
        if selected in ("all", "complaints"):
            complaints = self.moderation.complaint_repository.get_complaint_queue()
            ids = sorted({c.comment_id for c in complaints})
            self.app.views[2].show_tickets(complaints)
            body += '<h2>Жалобы</h2>'
            if not ids:
                body += '<p class="empty-state">Жалоб на рассмотрении нет.</p>'
            for comment_id in ids:
                comment = self.db.get(d.Comment, comment_id)
                if comment is None:
                    continue
                count = self.moderation.complaint_repository.get_complaint_count(comment_id)
                body += (f'<article><p>{escape_html(comment.text)}</p><small>Жалоб: {count}; статус: {escape_html(status_label(comment.status))}</small>'
                         f'<form method="post" action="/moderation/complaint/{escape_html(comment_id)}">{self._csrf()}'
                         '<button name="decision" value="confirm">Подтвердить удаление</button> '
                         '<button name="decision" value="dismiss">Отклонить жалобу и восстановить</button></form></article>')
        return body

    def _admin(self) -> str:
        body = '<h2>Рубрики</h2>'
        for rubric in self.db.list_entities(d.Category):
            body += (f'<form method="post" action="/admin/rubric">{self._csrf()}'
                     f'<input type="hidden" name="id" value="{escape_html(rubric.category_id)}">'
                     f'<input name="name" value="{escape_html(rubric.name)}" required> '
                     f'<input name="description" value="{escape_html(rubric.description)}"> '
                     '<button name="action" value="save">Сохранить</button> ')
            if not self.db.list_entities(d.Article, 'category_id=?', (rubric.category_id,)):
                body += '<button name="action" value="delete">Удалить</button>'
            body += '</form>'
        body += (f'<form method="post" action="/admin/rubric">{self._csrf()}'
                 '<input name="name" placeholder="Новая рубрика" required> '
                 '<input name="description" placeholder="Описание"><button name="action" value="save">Добавить</button></form>')
        roles = self.db.list_entities(d.Role)
        options = "".join(f'<option value="{escape_html(r.role_id)}">{escape_html(role_label(r.role_name))}</option>' for r in roles)
        body += '<h2>Пользователи и роли</h2>'
        for account in self.db.list_entities(d.UserAccount):
            body += (f'<form method="post" action="/admin/role">{self._csrf()}'
                     f'{escape_html(account.login)} <input type="hidden" name="account" value="{escape_html(account.account_id)}">'
                     '<select name="role">' + "".join(
                         f'<option value="{escape_html(r.role_id)}" {"selected" if r.role_id == account.role_id else ""}>{escape_html(role_label(r.role_name))}</option>'
                         for r in roles) + '</select><button>Назначить роль</button></form>')
        body += '<h2>Права ролей</h2>'
        for role_obj in roles:
            rights = self.db.list_entities(d.AccessPermission, 'role_id=?', (role_obj.role_id,))
            body += f'<p>{escape_html(role_label(role_obj.role_name))}: {escape_html(", ".join(r.operation_code for r in rights))}</p>'
            for right in rights:
                body += (f'<form method="post" action="/admin/permission" class="inline">{self._csrf()}'
                         f'<input type="hidden" name="role" value="{escape_html(role_obj.role_id)}">'
                         f'<input type="hidden" name="code" value="{escape_html(right.operation_code)}">'
                         f'<button name="action" value="remove">Убрать {escape_html(right.operation_code)}</button></form> ')
        body += (f'<form method="post" action="/admin/permission">{self._csrf()}'
                 f'<select name="role">{options}</select><input name="code" placeholder="Код операции" required>'
                 '<button name="action" value="add">Добавить право</button></form>')
        body += (f'<h2>Отчётность</h2><form method="post" action="/admin/report">{self._csrf()}'
                 '<label>Начало периода<input type="date" name="start" required></label>'
                 '<label>Конец периода<input type="date" name="end" required></label><button>Сформировать</button></form>')
        for report in self.reports.get_reports():
            body += (f'<p>{escape_html(report.period)}: публикаций {report.publication_count}, '
                     f'комментариев {report.comment_count}, реакций {report.reaction_count}, '
                     f'охват {report.reach_metric:g}</p>')
        return body

    def _media(self, media_id: str) -> tuple[str, bytes, list[tuple[str, str]]]:
        media = self.db.get(d.MediaAttachment, media_id)
        if media is None:
            raise d.NotFound(media_id)
        article = self.db.get(d.Article, media.article_id)
        if article is None or article.deleted_at is not None:
            raise d.NotFound(media.article_id)
        author = self._profile(d.ContentAuthor)
        if article.publication_status != d.ArticleStatus.PUBLISHED and not (
            author and author.author_id == article.author_id or has_permission(self.db, self.account, "article.moderate")
        ):
            raise d.PermissionDenied("Вложение не опубликовано")
        path = self._uploads() / media_id
        if not path.is_file():
            raise d.NotFound(media_id)
        return "200 OK", path.read_bytes(), [("Content-Type", media.content_type),
                                               ("X-Content-Type-Options", "nosniff")]

    def _uploads(self) -> Path:
        path = Path(self.db.path)
        return path.parent / "uploads" if self.db.path != ":memory:" else Path("/tmp/omis_blog_uploads")

    def _post(self, path: str, data: dict[str, str],
              files: list[tuple[str, bytes, str]]) -> tuple[str, str, list[tuple[str, str]]]:
        if path == "/login":
            key = data.get("login", "").strip().lower()
            now = time.monotonic()
            recent = [moment for moment in self.login_attempts.get(key, []) if now - moment < 300]
            if len(recent) >= 8:
                raise d.PermissionDenied("too_many_attempts")
            account = authenticate(self.db, data.get("login", ""), data.get("password", ""))
            if account is None:
                self.login_attempts[key] = recent + [now]
                raise d.PermissionDenied("invalid_credentials")
            self.login_attempts.pop(key, None)
            self._rotate_session(account.user_id)
            return self._redirect("/")
        if path == "/register":
            account = register_author(self.db, data.get("full_name", ""), data.get("login", ""),
                                      data.get("password", ""), data.get("confirmation", ""))
            self._rotate_session(account.user_id)
            return self._redirect("/my-articles")
        if path == "/logout":
            assert self.session
            self.db.delete(d.UserSession, self.session.session_id)
            self.ui_states.pop(self.session.session_id, None)
            self.cookie = self._cookie("") + "; Max-Age=0"
            return self._redirect("/login")
        if path == "/article/save":
            return self._save_article(data, files)
        if path.startswith("/article/") and path.endswith("/delete"):
            article_id = path.split("/")[2]
            article = self.db.get(d.Article, article_id)
            if article is None or article.deleted_at is not None:
                raise d.NotFound(article_id)
            if not self._can_delete_article(article):
                raise d.PermissionDenied("article_delete_denied")
            assert self.account is not None
            if not self.db.soft_delete_article(article_id, self.account.user_id):
                raise d.NotFound(article_id)
            return self._redirect("/my-articles" if has_permission(self.db, self.account, "article.write") else "/")
        if path.startswith("/article/") and path.endswith("/status"):
            self._require("article.moderate")
            article_id = path.split("/")[2]
            article = self.db.get(d.Article, article_id)
            if article is None or article.deleted_at is not None:
                raise d.NotFound(article_id)
            article.transition_to(d.ArticleStatus(data.get("status", "")))
            self.db.save(article)
            return self._redirect("/article/" + article_id)
        if path.startswith("/article/"):
            return self._social(path, data)
        if path.startswith("/media/") and path.endswith("/delete"):
            return self._delete_media(path.split("/")[2])
        if path.startswith("/moderation/article/"):
            self._require("article.moderate")
            article_id = path.split("/")[3]
            editor = self._profile(d.Editor)
            if editor is None:
                raise d.PermissionDenied("Нет профиля редактора")
            if data.get("decision") == "approve":
                self.publications.publish_material(article_id, editor.editor_id)
            elif data.get("decision") == "reject":
                self.publications.return_for_revision(article_id, editor.editor_id, data.get("note", ""))
            else:
                raise d.DomainException("Неизвестное решение")
            return self._redirect("/moderation")
        if path.startswith("/moderation/priority/"):
            self._require("article.moderate")
            ticket_id = path.split("/")[3]
            ticket = self.db.get(d.ModerationQueueEntry, ticket_id)
            if ticket is None or ticket.processed_at is not None:
                raise d.NotFound(ticket_id)
            article = self.db.get(d.Article, ticket.article_id)
            if article is None or article.deleted_at is not None:
                raise d.NotFound(ticket_id)
            priority = int(data.get("priority", "0"))
            if not 0 <= priority <= 10:
                raise d.DomainException("Приоритет от 0 до 10")
            ticket.priority = priority
            self.db.save(ticket)
            return self._redirect("/moderation")
        if path.startswith("/moderation/complaint/"):
            self._require("article.moderate")
            decision = data.get("decision", "")
            if decision is None:
                raise d.DomainException("Неизвестное решение")
            self.moderation.apply_decision(decision, path.split("/")[3])
            return self._redirect("/moderation")
        if path.startswith("/admin/"):
            self._require("admin")
            return self._admin_post(path, data)
        raise d.NotFound(path)

    def _save_article(self, data: dict[str, str], files: list[tuple[str, bytes, str]]) -> tuple[str, str, list[tuple[str, str]]]:
        self._require("article.write")
        author = self._profile(d.ContentAuthor)
        if author is None:
            raise d.PermissionDenied("Нет профиля автора")
        article_id = data.get("id", "")
        article = self.db.get(d.Article, article_id) if article_id else d.Article(author_id=author.author_id)
        if article is None or article.deleted_at is not None:
            raise d.NotFound(article_id)
        if article.author_id != author.author_id or article.publication_status not in (
            d.ArticleStatus.DRAFT, d.ArticleStatus.NEEDS_REVISION
        ):
            raise d.PermissionDenied("Редактировать можно только свой черновик")
        signatures = {
            "image/png": lambda p: p.startswith(b"\x89PNG\r\n\x1a\n"),
            "image/jpeg": lambda p: p.startswith(b"\xff\xd8\xff"),
            "application/pdf": lambda p: p.startswith(b"%PDF-"),
        }
        for _, payload, mime in files:
            if payload and (mime not in signatures or len(payload) > 5_000_000 or not signatures[mime](payload)):
                raise d.DomainException("Недопустимый тип или размер файла")
        article.title = data.get("title", "").strip()
        article.content = data.get("content", "")
        article.category_id = data.get("rubric", "")
        if article.category_id and not self.db.get(d.Category, article.category_id):
            raise d.DomainException("Рубрика не существует")
        article.classified_at = d.utc_now() if article.category_id else None
        self.db.save(article)
        tags = []
        for name in {x.strip() for x in data.get("tags", "").split(",") if x.strip()}:
            found = self.db.list_entities(d.Tag, 'keyword=?', (name,))
            tags.append(found[0] if found else d.Tag(keyword=name))
        self.db.set_article_tags(article.article_id, tags)
        style = self.db.list_entities(d.FormattingOptions, 'article_id=?', (article.article_id,))
        style_id = style[0].formatting_id if style else d.new_id()
        self.db.save(d.FormattingOptions(
            formatting_id=style_id,
            font=data.get("font", "system") if data.get("font") in ("system", "serif") else "system",
            has_preview=data.get("preview") == "on", article_id=article.article_id))
        article.formatting_id = style_id
        self.db.save(article)
        for filename, payload, mime in files:
            if not payload:
                continue
            attachment = d.MediaAttachment(file_url=Path(filename).name,
                                        content_type=mime, size=len(payload), article_id=article.article_id)
            self._uploads().mkdir(parents=True, exist_ok=True)
            (self._uploads() / attachment.media_id).write_bytes(payload)
            self.db.save(attachment)
        action = data.get("action", "draft")
        if action == "submit":
            self.publications.process_submission(article)
        if action == "autosave":
            self.app.views[1].show_autosave_status("Автосохранено")
            self.ui.autosaved_at = d.utc_now()
            return "200 OK", "Автосохранено", [("Content-Type", "text/plain; charset=utf-8"),
                                                 ("X-Article-ID", article.article_id)]
        return self._redirect(f"/editor/{article.article_id}") if action == "draft" else self._redirect("/")

    def _delete_media(self, media_id: str) -> tuple[str, str, list[tuple[str, str]]]:
        self._require("article.write")
        media = self.db.get(d.MediaAttachment, media_id)
        if media is None:
            raise d.NotFound(media_id)
        article = self.db.get(d.Article, media.article_id)
        author = self._profile(d.ContentAuthor)
        if not article or article.deleted_at is not None or not author or article.author_id != author.author_id:
            raise d.PermissionDenied("Чужое вложение")
        self.db.delete(d.MediaAttachment, media_id)
        (self._uploads() / media_id).unlink(missing_ok=True)
        return self._redirect(f"/editor/{article.article_id}")

    def _social(self, path: str, data: dict[str, str]) -> tuple[str, str, list[tuple[str, str]]]:
        if not self.account:
            raise d.PermissionDenied("Войдите")
        _, _, article_id, action = path.split("/", 3)
        article = self.db.get(d.Article, article_id)
        if not article or article.deleted_at is not None or article.publication_status != d.ArticleStatus.PUBLISHED:
            raise d.PermissionDenied("Статья не опубликована")
        reader = self._profile(d.Reader)
        if reader is None:
            raise d.PermissionDenied("Нет профиля читателя")
        if action == "comment":
            self._require("comment.write")
            text = data.get("text", "").strip()
            parent_id = data.get("parent", "")
            if not text:
                raise d.DomainException("Пустой комментарий")
            if parent_id:
                parent = self.db.get(d.Comment, parent_id)
                if not parent or parent.article_id != article_id or parent.status != d.CommentStatus.VISIBLE:
                    raise d.DomainException("Недопустимый ответ")
            self.db.save(d.Comment(
                text=text, article_id=article_id, reader_id=reader.reader_id,
                parent_id=parent_id, replied_at=d.utc_now() if parent_id else None))
        elif action == "react":
            self._require("reaction.write")
            reaction_type = d.ReactionType(data.get("type", "like"))
            existing = self.db.list_entities(d.Reaction, 'article_id=? AND reader_id=?',
                                      (article_id, reader.reader_id))
            reaction = existing[0] if existing else d.Reaction(article_id=article_id, reader_id=reader.reader_id)
            reaction.reaction_type = reaction_type
            reaction.marked_at = d.utc_now()
            self.db.save(reaction)
        elif action == "report":
            self._require("comment.write")
            comment = self.db.get(d.Comment, data.get("comment", ""))
            if not comment or comment.article_id != article_id:
                raise d.DomainException("Комментарий не найден")
            reason = data.get("reason", "").strip()
            if not reason:
                raise d.DomainException("Причина обязательна")
            self.moderation.register_complaint(d.Complaint(
                reason=reason, comment_id=comment.comment_id, reader_id=reader.reader_id))
        else:
            raise d.NotFound(path)
        return self._redirect(f"/article/{article_id}")

    def _admin_post(self, path: str, data: dict[str, str]) -> tuple[str, str, list[tuple[str, str]]]:
        if path == "/admin/rubric":
            rubric_id = data.get("id", "")
            if data.get("action") == "delete":
                if self.db.list_entities(d.Article, 'category_id=?', (rubric_id,)):
                    raise d.DomainException("Рубрика используется статьями")
                self.db.delete(d.Category, rubric_id)
            else:
                name = data.get("name", "").strip()
                if not name:
                    raise d.DomainException("Название обязательно")
                rubric = self.db.get(d.Category, rubric_id) if rubric_id else d.Category()
                if rubric is None:
                    raise d.NotFound(rubric_id)
                admin = self._profile(d.PlatformAdministrator)
                rubric.name, rubric.description = name, data.get("description", "")
                rubric.administrator_id = admin.administrator_id if admin else ""
                rubric.modified_at = d.utc_now()
                self.db.save(rubric)
        elif path == "/admin/role":
            account = self.db.get(d.UserAccount, data.get("account", ""))
            role_obj = self.db.get(d.Role, data.get("role", ""))
            if account is None or role_obj is None:
                raise d.NotFound("Учётная запись или роль")
            account.role_id = role_obj.role_id
            self.db.save(account)
            self._ensure_profiles(account)
        elif path == "/admin/permission":
            role_obj = self.db.get(d.Role, data.get("role", ""))
            code = data.get("code", "").strip()
            if role_obj is None or not code:
                raise d.DomainException("Нужны роль и код операции")
            existing = self.db.list_entities(d.AccessPermission, 'role_id=? AND operation_code=?',
                                      (role_obj.role_id, code))
            if data.get("action") == "remove":
                for right in existing:
                    self.db.delete(d.AccessPermission, right.permission_id)
            elif not existing:
                self.db.save(d.AccessPermission(operation_code=code, role_id=role_obj.role_id))
                for account in self.db.list_entities(d.UserAccount, 'role_id=?', (role_obj.role_id,)):
                    self._ensure_profiles(account)
        elif path == "/admin/report":
            report = self.reports.generate_report(f'{data.get("start", "")}/{data.get("end", "")}')
            admin = self._profile(d.PlatformAdministrator)
            report.administrator_id = admin.administrator_id if admin else ""
            self.db.save(report)
        else:
            raise d.NotFound(path)
        return self._redirect("/admin")

    def _ensure_profiles(self, account: d.UserAccount) -> None:
        user = self.db.get(d.User, account.user_id)
        if user is None:
            raise d.NotFound(account.user_id)
        rights = {right.operation_code for right in self.db.list_entities(
            d.AccessPermission, 'role_id=?', (account.role_id,))}
        definitions = (
            (d.ContentAuthor, "article.write", lambda: d.ContentAuthor(full_name=user.full_name,
                                                                      user_id=user.user_id)),
            (d.Editor, "article.moderate", lambda: d.Editor(full_name=user.full_name,
                                                                 user_id=user.user_id)),
            (d.PlatformAdministrator, "admin", lambda: d.PlatformAdministrator(
                full_name=user.full_name, access_level="Назначенный", user_id=user.user_id)),
        )
        for cls, operation, create in definitions:
            if operation in rights and not self.db.list_entities(cls, 'user_id=?', (user.user_id,)):
                self.db.save(create())
