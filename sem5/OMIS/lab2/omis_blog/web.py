"""Local WSGI presentation for the corporate blog."""

from __future__ import annotations

import html
import re
import sqlite3
import time
from collections import Counter
from datetime import timedelta
from pathlib import Path
from email.parser import BytesParser
from email.policy import default
from typing import Any, Callable
from urllib.parse import parse_qs, urlencode

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
    def inline(text: str) -> str:
        return re.sub(r'\*\*([^*]+)\*\*|\*([^*]+)\*',
                      lambda match: f'<strong>{match[1]}</strong>' if match[1] else f'<em>{match[2]}</em>',
                      escape_html(text))
    for line in value.splitlines():
        line = line.strip()
        if not line:
            flush()
        elif line.startswith("### "):
            flush()
            blocks.append("<h3>" + inline(line[4:]) + "</h3>")
        elif line.startswith("## "):
            flush()
            blocks.append("<h2>" + inline(line[3:]) + "</h2>")
        elif line.startswith("# "):
            flush()
            blocks.append("<h2>" + inline(line[2:]) + "</h2>")
        else:
            paragraph.append(inline(line))
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
        data: dict[str, str] = {}
        csrf_valid = False
        try:
            if method == "POST":
                data, files = form_data(environ)
                if not self.session or data.get("csrf") != self.session.authorization_token:
                    raise d.PermissionDenied("Неверный токен формы")
                csrf_valid = True
                status, body, headers = self._post(path, data, files)
            else:
                status, body, headers = self._get(path)
        except d.PermissionDenied as exc:
            status, body, headers = self._form_error(path, data, exc, "403 Forbidden") if csrf_valid else ("403 Forbidden", self._page("Нет доступа", f'<p role="alert">{escape_html(error_message(str(exc)))}</p>'), [])
        except d.NotFound as exc:
            status, body, headers = self._form_error(path, data, exc, "404 Not Found") if csrf_valid else ("404 Not Found", self._page("Не найдено", f"<p>{escape_html(exc)}</p>"), [])
        except (d.DomainException, sqlite3.IntegrityError, ValueError) as exc:
            status, body, headers = self._form_error(path, data, exc, "400 Bad Request") if csrf_valid else ("400 Bad Request", self._page("Ошибка", f'<p role="alert">{escape_html(error_message(str(exc)))}</p>'), [])
        if self.cookie:
            headers.append(("Set-Cookie", self.cookie))
        if not any(k.lower() == "content-type" for k, _ in headers):
            headers.append(("Content-Type", "text/html; charset=utf-8"))
        start_response(status, headers)
        return [body if isinstance(body, bytes) else body.encode("utf-8")]

    def _form_error(self, path: str, data: dict[str, str], exc: Exception,
                    status: str) -> tuple[str, str, list[tuple[str, str]]]:
        message = error_message(str(exc))
        alert = f'<p class="form-error" role="alert">{escape_html(message)}</p>'
        if path in ("/login", "/register"):
            title = "Вход" if path == "/login" else "Регистрация"
            return status, self._page(title, self._auth_form(path, data, alert)), []
        if path == "/article/save" and data.get("action") != "autosave":
            try:
                self._require("article.write")
                return status, self._page("Редактор публикации", self._editor(data.get("id") or "new", data, alert), layout="editor"), []
            except (d.DomainException, ValueError):
                pass
        if path.startswith("/moderation/") and has_permission(self.db, self.account, "article.moderate"):
            self.params["filter"] = "complaints" if "/complaint/" in path else "articles"
            return status, self._page("Кабинет редактора", alert + self._moderation(data), layout="moderation"), []
        if path.startswith("/admin/") and has_permission(self.db, self.account, "admin"):
            return status, self._page("Администрирование", alert + self._admin(data, path)), []
        return status, self._page("Ошибка", alert), []

    def _auth_form(self, path: str, data: dict[str, str], alert: str = "") -> str:
        login = escape_html(data.get("login", ""))
        if path == "/login":
            return (f'<form class="auth-form" method="post" action="/login">{self._csrf()}{alert}'
                    f'<label>Логин <input name="login" value="{login}" autocomplete="username" required></label>'
                    '<label>Пароль <input type="password" name="password" autocomplete="current-password" required></label>'
                    '<button class="primary">Войти</button><p>Нет учётной записи? <a href="/register">Зарегистрироваться</a></p></form>')
        name = escape_html(data.get("full_name", ""))
        return (f'<form class="auth-form" method="post" action="/register">{self._csrf()}{alert}'
                f'<label>ФИО <input name="full_name" value="{name}" maxlength="120" autocomplete="name" required></label>'
                f'<label>Логин <input name="login" value="{login}" minlength="3" maxlength="40" autocomplete="username" required></label>'
                '<label>Пароль <input type="password" name="password" minlength="10" maxlength="128" autocomplete="new-password" required></label>'
                '<label>Повторите пароль <input type="password" name="confirmation" minlength="10" maxlength="128" autocomplete="new-password" required></label>'
                '<button class="primary">Создать аккаунт</button><p>Уже есть аккаунт? <a href="/login">Войти</a></p></form>')

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

    def _header(self, layout: str) -> str:
        nav = [self._navigation_link("Лента публикаций", "/")]
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
        if not layout and has_permission(self.db, self.account, "article.write"):
            writing_action = self._navigation_link("Написать статью", "/editor/new", "button button-primary")
        context = {
            "editor": '<a href="/my-articles">Мои статьи</a><span class="workspace-title">Редактор публикации</span>'
                      '<span id="autosave" class="muted" role="status" aria-live="polite">Автосохранение</span>',
            "moderation": '<span class="workspace-title">Панель модератора</span>',
            "reading": '<a class="back-to-feed" href="/">← К ленте</a>',
        }.get(layout, "")
        search = ""
        if layout == "feed":
            search = (f'<form class="header-search" method="get" action="/" role="search">'
                      f'<input name="q" type="search" aria-label="Поиск по статьям" placeholder="Поиск по статьям" value="{escape_html(self.params.get("q"))}">'
                      + ''.join(f'<input type="hidden" name="{key}" value="{escape_html(self.params.get(key))}">'
                                for key in ("author", "rubric", "tag"))
                      + '<button type="submit">Найти</button></form>')
        return (
            '<header class="site-header"><div class="header-inner">'
            '<a class="brand" href="/" aria-label="Корпоративный блог — главная">'
            '<span class="brand-mark" aria-hidden="true">КБ</span><span>КОРП-БЛОГ</span></a>'
            + (f'<div class="header-context">{context}</div>' if context else
               f'<nav class="primary-navigation" aria-label="Основная навигация">{"".join(nav)}</nav>')
            + f'<div class="header-actions">{search}{writing_action}{account_actions}</div>'
            '</div></header>'
        )

    def _page(self, title: str, body: str, subtitle: str = "", layout: str = "") -> str:
        role_name = role(self.db, self.account)
        role_display = f'<p class="role-label">{escape_html(role_label(role_name))}</p>' if role_name else ""
        subtitle_html = f'<p class="page-subtitle">{escape_html(subtitle)}</p>' if subtitle else ""
        heading = (f'<header class="page-heading"><h1>{escape_html(title)}</h1>{subtitle_html}{role_display}</header>'
                   if not layout else f'<h1 class="visually-hidden">{escape_html(title)}</h1>' if layout != "reading" else "")
        footer = ('<footer class="site-footer"><div class="footer-inner">'
                  '<span>Корпоративный блог</span><span>Идеи, новости и опыт нашей команды</span>'
                  '</div></footer>') if not layout else ''
        return (
            '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape_html(title)} · Корпоративный блог</title>'
            f'<link rel="stylesheet" href="/assets/site.css"></head><body class="{"prototype-page layout-" + layout if layout else ""}">'
            f'{self._header(layout)}<main class="site-main">{heading}'
            f'<div class="page-content">{body}</div></main>{footer}</body></html>'
        )

    @staticmethod
    def _redirect(path: str) -> tuple[str, str, list[tuple[str, str]]]:
        return "303 See Other", "", [("Location", path)]

    def _get(self, path: str) -> tuple[str, str | bytes, list[tuple[str, str]]]:
        if path == "/assets/editor.js":
            return "200 OK", Path(__file__).with_name("editor.js").read_bytes(), [("Content-Type", "application/javascript; charset=utf-8")]
        if path == "/assets/site.css":
            return "200 OK", Path(__file__).with_name("site.css").read_bytes(), [("Content-Type", "text/css; charset=utf-8")]
        if path in ("/login", "/register"):
            return "200 OK", self._page("Вход" if path == "/login" else "Регистрация", self._auth_form(path, {})), []
        if path == "/":
            return "200 OK", self._page("Лента статей", self._feed(), layout="feed"), []
        if path == "/my-articles":
            self._require("article.write")
            return "200 OK", self._page("Мои статьи", self._my_articles()), []
        if path.startswith("/article/"):
            return "200 OK", self._page("Статья", self._article(path.split("/")[2]), layout="reading"), []
        if path.startswith("/editor/"):
            self._require("article.write")
            return "200 OK", self._page("Редактор публикации", self._editor(path.split("/")[2]), layout="editor"), []
        if path == "/moderation":
            self._require("article.moderate")
            return "200 OK", self._page("Кабинет редактора", self._moderation(), layout="moderation"), []
        if path == "/admin":
            self._require("admin")
            return "200 OK", self._page("Администрирование", self._admin()), []
        if path == "/notifications":
            if not self.account:
                raise d.PermissionDenied("Войдите")
            body = "".join(f'<article class="list-card notification-card"><p>{escape_html(row["text"])}</p><time class="muted">{escape_html(row["created_at"])}</time></article>'
                           for row in self.notices.inbox(self.account.user_id))
            return "200 OK", self._page("Уведомления", body or '<p class="empty-state">Пока нет уведомлений.</p>'), []
        if path.startswith("/media/"):
            return self._media(path.split("/")[2])
        raise d.NotFound(path)

    def _feed(self) -> str:
        page = max(1, int(self.params.get("page", "1")))
        query = self.params.get("q", "")
        author = self.params.get("author", "")
        rubric = self.params.get("rubric", "")
        tag = self.params.get("tag", "")
        published = self.feed.article_repository.get_recent_publications()
        matching = self.feed.search(query, author, rubric, tag, size=len(published))
        page_count = max(1, (len(matching) + 9) // 10)
        articles = matching[(page - 1) * 10:page * 10]
        view = self.app.views[0]
        view.state.current_page = page
        view.state.selected_filter = rubric
        view.display_feed(articles)
        self.ui.feed_updated_at = d.utc_now()
        if rubric:
            self.ui.filter_applied_at = d.utc_now()
        categories = self.db.list_entities(d.Category, order="name")

        def feed_link(**changes: str | int) -> str:
            fields = {"q": query, "author": author, "rubric": rubric, "tag": tag, **changes}
            return escape_html("/?" + urlencode({key: value for key, value in fields.items() if value}))

        category_marker = ' aria-current="true"'
        chips = "".join(
            f'<a class="filter-chip" href="{feed_link(rubric=key)}"'
            f'{category_marker if key == rubric else ""}>{escape_html(label)}</a>'
            for key, label in [("", "Все рубрики"), *((item.category_id, item.name) for item in categories)])
        write = ('<a class="button button-success" href="/editor/new">+ Написать статью</a>'
                 if has_permission(self.db, self.account, "article.write") else '')
        body = (f'<div class="feed-filter-bar"><nav aria-label="Рубрики">{chips}</nav>{write}</div>'
                f'<details class="advanced-search"{" open" if author or tag else ""}><summary>Фильтры поиска</summary>'
                '<form method="get" action="/" aria-label="Фильтры поиска">'
                f'<input type="hidden" name="q" value="{escape_html(query)}">'
                f'<input type="hidden" name="rubric" value="{escape_html(rubric)}">'
                f'<label>Автор<input name="author" value="{escape_html(author)}"></label>'
                f'<label>Тег<input name="tag" value="{escape_html(tag)}"></label>'
                '<button type="submit">Применить</button><a href="/">Сбросить</a></form></details>'
                '<div class="feed-columns"><section class="feed-list" aria-label="Публикации">')
        if articles:
            body += "".join(self._article_card(article) for article in articles)
        else:
            body += ('<section class="empty-state" aria-live="polite"><h2>По этому запросу пока ничего нет</h2>'
                     '<p>Измените слова поиска или выберите другую рубрику.</p>'
                     '<a class="button button-secondary" href="/">Сбросить фильтры</a></section>')
        if articles:
            current_marker = ' aria-current="page"'
            body += '<nav class="feed-pagination" aria-label="Страницы ленты">'
            if page > 1:
                body += f'<a href="{feed_link(page=page-1)}">Назад</a>'
            for index in range(max(1, page - 2), min(page_count, page + 2) + 1):
                body += f'<a href="{feed_link(page=index)}"{current_marker if index == page else ""}>{index}</a>'
            if page < page_count:
                body += f'<a href="{feed_link(page=page+1)}">Далее</a>'
            body += '</nav>'
        tag_counts = Counter(item.keyword for article in published for item in self.db.get_article_tags(article.article_id))
        popular = "".join(f'<a href="{feed_link(tag=keyword)}">#{escape_html(keyword)} <span>{count}</span></a>'
                          for keyword, count in tag_counts.most_common(5))
        week_start = d.utc_now() - timedelta(days=7)
        recent = sum(item.published_at is not None and item.published_at >= week_start for item in published)
        author_views: Counter[str] = Counter()
        for item in published:
            author_views[item.author_id] += item.view_count
        leading = author_views.most_common(1)
        leading_author = self.db.get(d.ContentAuthor, leading[0][0]) if leading and leading[0][1] > 0 else None
        links = (self._navigation_link("Мои статьи", "/my-articles")
                 if has_permission(self.db, self.account, "article.write") else '')
        if self.account:
            links += self._navigation_link("Уведомления", "/notifications")
        else:
            links = self._navigation_link("Вход", "/login") + self._navigation_link("Регистрация", "/register")
        return (body + '</section><aside class="feed-sidebar" aria-label="Дополнительно">'
                '<section class="prototype-panel"><h2>Популярные рубрики</h2>'
                f'<div class="tag-cloud">{popular or "Пока нет популярных тегов."}</div></section>'
                '<section class="prototype-panel"><h2>Статистика активности</h2><dl class="feed-stats">'
                f'<div><dt>Статей за неделю</dt><dd>{recent}</dd></div>'
                f'<div><dt>Самый читаемый автор</dt><dd>{escape_html(leading_author.full_name if leading_author else "—")}</dd></div>'
                '</dl></section>'
                f'<section class="prototype-panel"><h2>Быстрые ссылки</h2><div class="sidebar-links">{links}</div></section></aside></div>')

    def _article_card(self, article: d.Article) -> str:
        author = self.db.get(d.ContentAuthor, article.author_id)
        category = self.db.get(d.Category, article.category_id)
        category_name = category.name if category else "Блог"
        options = self.db.list_entities(d.FormattingOptions, 'article_id=?', (article.article_id,))
        show_preview = options[0].has_preview if options else True
        reactions = len(self.db.list_entities(d.Reaction, 'article_id=?', (article.article_id,)))
        comments = len(self.db.list_entities(d.Comment, 'article_id=? AND status=?',
                                             (article.article_id, d.CommentStatus.VISIBLE.value)))
        preview_text = article.summary or re.sub(r"[#*]", "", article.content)[:220]
        date = article.published_at.date().isoformat() if article.published_at else ""
        department = f' ({escape_html(author.department)})' if author and author.department else ''
        url = f'/article/{escape_html(article.article_id)}'
        return (
            '<article class="prototype-panel feed-card"><header>'
            f'<h2><a href="{url}">{escape_html(article.title)}</a></h2>'
            f'<span class="category-pill">{escape_html(category_name)}</span></header>'
            f'<p class="card-meta">{escape_html(author.full_name if author else "Автор")}{department} · {escape_html(date)}</p>'
            + (f'<p class="article-excerpt">{escape_html(preview_text)}</p>' if show_preview else '')
            + f'<footer><a href="{url}">Читать далее →</a>'
            + f'<span class="card-counts"><span>👍 {reactions}<span class="visually-hidden"> реакций</span></span>'
            + f'<span>▤ {comments}<span class="visually-hidden"> комментариев</span></span></span></footer></article>'
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
        body = '<p><a class="button button-primary" href="/editor/new">Создать статью</a></p>' + links + '<div class="my-articles">'
        for item in articles:
            editable = item.publication_status in (d.ArticleStatus.DRAFT, d.ArticleStatus.NEEDS_REVISION)
            category = self.db.get(d.Category, item.category_id)
            href = f'/editor/{escape_html(item.article_id)}' if editable else f'/article/{escape_html(item.article_id)}'
            body += (f'<article class="list-card"><span class="status-badge">{escape_html(status_label(item.publication_status))}</span>'
                     f'<h2><a href="{href}">{escape_html(item.title or "Без названия")}</a></h2>'
                     f'<p class="muted">Создано {escape_html(item.created_at.date())} · {escape_html(category.name if category else "Без рубрики")}</p>'
                     f'<a class="button" href="{href}">{"Редактировать" if editable else "Просмотреть"}</a>')
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
                'onsubmit="return confirm(&quot;Удалить статью? Она исчезнет из ленты и списков. Это действие нельзя отменить.&quot;)">'
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
        body = (f'<article class="article-reading"><header class="prototype-panel reading-heading">'
                f'<p class="category-pill">{escape_html(category.name if category else "Блог")}</p>'
                f'<h1 class="reading-title">{escape_html(article.title)}</h1>'
                + (f'<p class="article-summary">{escape_html(article.summary)}</p>' if article.summary else '') +
                '<div class="article-byline">'
                f'<span>{escape_html(author_record.full_name if author_record else "Автор")}</span>'
                f'<time datetime="{escape_html(article.published_at.isoformat() if article.published_at else "")}">{escape_html(article_date)}</time>'
                f'<span>Просмотры: {article.view_count}</span></div>')
        if article.publication_status != d.ArticleStatus.PUBLISHED:
            body += f'<p class="muted">Статус: {escape_html(status_label(article.publication_status))}</p>'
        body += ('</header><section class="prototype-panel reading-content" aria-label="Текст статьи">'
                f'<div class="article-body font-{font}" style="font-family:{font}">{render_markdown(article.content)}</div>')
        tags = self.db.get_article_tags(article_id)
        if tags:
            body += '<p class="muted">Теги: ' + ', '.join(escape_html(tag.keyword) for tag in tags) + '</p>'
        for media in self.db.list_entities(d.MediaAttachment, 'article_id=?', (article_id,)):
            if media.content_type.startswith("image/"):
                body += (f'<figure class="article-media"><img src="/media/{escape_html(media.media_id)}" '
                         f'alt="Иллюстрация к статье: {escape_html(article.title)}"></figure>')
            body += f'<p><a href="/media/{escape_html(media.media_id)}">Вложение: {escape_html(media.file_url)}</a></p>'
        body += '</section>'
        if article.publication_status == d.ArticleStatus.PUBLISHED:
            reactions = self.db.list_entities(d.Reaction, 'article_id=?', (article_id,))
            comments = self.db.list_entities(d.Comment, 'article_id=?', (article_id,), 'added_at')
            visible_comments = [comment for comment in comments if comment.status == d.CommentStatus.VISIBLE]
            counts = Counter(item.reaction_type for item in reactions)
            options = ((d.ReactionType.LIKE, "👍 Нравится"), (d.ReactionType.HELPFUL, "★ Полезно"))
            body += '<section class="article-engagement" aria-label="Реакции">'
            if has_permission(self.db, self.account, "reaction.write"):
                reader = self._profile(d.Reader)
                selected = next((item.reaction_type for item in reactions if reader and item.reader_id == reader.reader_id), None)
                body += (f'<form method="post" action="/article/{escape_html(article_id)}/react">{self._csrf()}'
                         + ''.join(f'<button name="type" value="{kind.value}" aria-pressed="{str(kind == selected).lower()}">'
                                   f'{label} · {counts[kind]}</button>' for kind, label in options) + '</form>')
            else:
                body += ''.join(f'<span>{label} · {counts[kind]}</span>' for kind, label in options)
            body += '</section>'
            self.app.views[3].display_comments(comments)
            can_comment = has_permission(self.db, self.account, "comment.write")
            body += f'<section class="comments-section prototype-panel"><h2>Комментарии <span class="heading-count">{len(visible_comments)}</span></h2>'
            if not visible_comments:
                body += '<p class="empty-state">Пока нет комментариев. Начните обсуждение.</p>'
            for comment in comments:
                text = escape_html(comment.text) if comment.status == d.CommentStatus.VISIBLE else '[Комментарий скрыт]'
                reply_class = " comment-reply" if comment.parent_id else ""
                commenter = self.db.get(d.Reader, comment.reader_id) if comment.status == d.CommentStatus.VISIBLE else None
                username = commenter.full_name if commenter else "Комментарий"
                author_badge = ('<span class="category-pill">Автор</span>' if commenter and commenter.user_id and author_record and
                                commenter.user_id == author_record.user_id else '')
                body += (f'<article class="comment-card{reply_class}" id="c-{escape_html(comment.comment_id)}">'
                         f'<header><strong>{escape_html(username)}</strong>{author_badge}'
                         f'<time datetime="{escape_html(comment.added_at.isoformat())}">{escape_html(comment.added_at.date())}</time></header>')
                if comment.parent_id:
                    parent = self.db.get(d.Comment, comment.parent_id)
                    parent_label = (
                        parent.text[:72]
                        if parent and parent.status == d.CommentStatus.VISIBLE
                        else "скрытый комментарий"
                    )
                    body += f'<small class="reply-context">В ответ на: {escape_html(parent_label)}</small>'
                body += f'<p>{text}</p>'
                if can_comment and comment.status == d.CommentStatus.VISIBLE:
                    body += (f'<details><summary>Ответить</summary><form method="post" action="/article/{escape_html(article_id)}/comment">{self._csrf()}'
                             f'<input type="hidden" name="parent" value="{escape_html(comment.comment_id)}">'
                             '<label>Ответ<textarea name="text" required rows="2"></textarea></label>'
                             '<button class="button button-quiet" type="submit">Отправить ответ</button></form></details>'
                             f'<details><summary>Пожаловаться</summary><form method="post" action="/article/{escape_html(article_id)}/report">{self._csrf()}'
                             f'<input type="hidden" name="comment" value="{escape_html(comment.comment_id)}">'
                             '<label>Причина жалобы<input name="reason" required></label>'
                             '<button class="button button-quiet" type="submit">Отправить жалобу</button></form></details>')
                body += '</article>'
            if can_comment:
                body += (f'<form method="post" action="/article/{escape_html(article_id)}/comment">{self._csrf()}'
                         '<label>Ваш комментарий<textarea name="text" required rows="4"></textarea></label>'
                         '<button class="button button-primary" type="submit">Отправить комментарий</button></form>')
            elif not self.account:
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

    def _editor(self, article_id: str, data: dict[str, str] | None = None, alert: str = "") -> str:
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
        if data is not None:
            article.title = data.get("title", "")
            article.content = data.get("content", "")
            article.category_id = data.get("rubric", "")
        rubric_options = '<option value="">Выберите рубрику</option>' + "".join(
            f'<option value="{escape_html(r.category_id)}" {"selected" if r.category_id == article.category_id else ""}>{escape_html(r.name)}</option>'
            for r in self.db.list_entities(d.Category))
        if article.category_id and not self.db.get(d.Category, article.category_id):
            rubric_options += (f'<option value="{escape_html(article.category_id)}" selected>'
                               'Недоступная рубрика</option>')
        tags = ", ".join(t.keyword for t in self.db.get_article_tags(article.article_id)) if article_id != "new" else ""
        style = self.db.list_entities(d.FormattingOptions, 'article_id=?', (article.article_id,))
        font = style[0].font if style else "system"
        preview = style[0].has_preview if style else True
        if data is not None:
            tags = data.get("tags", "")
            font = data.get("font", "system")
            preview = data.get("preview") == "on"
        attachments = []
        detached_forms = []
        if article_id != "new":
            for media in self.db.list_entities(d.MediaAttachment, 'article_id=?', (article.article_id,)):
                media_id = escape_html(media.media_id)
                attachments.append(f'<li><a href="/media/{media_id}">{escape_html(media.file_url)}</a>'
                                   f'<button type="submit" form="remove-{media_id}">Удалить вложение</button></li>')
                detached_forms.append(f'<form id="remove-{media_id}" method="post" action="/media/{media_id}/delete">'
                                      f'{self._csrf()}</form>')
        body = (f'<form id="editor" class="editor-workspace" method="post" action="/article/save" enctype="multipart/form-data">{self._csrf()}{alert}'
                f'<input type="hidden" name="id" value="{escape_html(article_id if article_id != "new" else "")}">'
                '<section class="prototype-panel editor-fields" aria-label="Поля статьи">'
                f'<label>Заголовок статьи<input name="title" value="{escape_html(article.title)}"></label>'
                '<div class="editor-field-row">'
                f'<label>Рубрика<select name="rubric">{rubric_options}</select></label>'
                f'<label>Теги (через запятую)<input name="tags" value="{escape_html(tags)}"></label></div>'
                '</section><section class="prototype-panel editor-canvas" aria-label="Содержание и вложения">'
                '<div class="editor-tools" role="group" aria-label="Форматирование">'
                '<button type="button" data-markdown="bold" aria-label="Полужирный"><strong>Ж</strong></button>'
                '<button type="button" data-markdown="italic" aria-label="Курсив"><em>К</em></button>'
                '<button type="button" data-markdown="heading" aria-label="Подзаголовок">H₂</button>'
                f'<label>Шрифт<select name="font"><option value="system" {"selected" if font == "system" else ""}>Системный</option>'
                f'<option value="serif" {"selected" if font == "serif" else ""}>С засечками</option></select></label>'
                f'<label class="editor-preview"><input type="checkbox" name="preview" {"checked" if preview else ""}>Превью в ленте</label></div>'
                f'<label class="editor-text"><span class="visually-hidden">Содержание</span><textarea name="content" placeholder="Начните писать статью…">{escape_html(article.content)}</textarea></label>'
                '<section class="editor-attachments"><h2>Прикреплённые файлы</h2>'
                + (f'<ul>{"".join(attachments)}</ul>' if attachments else '<p class="muted">Файлы пока не прикреплены.</p>')
                + '<label>Добавить файл (PNG, JPEG, PDF; до 5 МБ)<input type="file" name="media" accept="image/png,image/jpeg,application/pdf"></label>'
                '</section></section><div class="editor-action-bar">'
                f'<span class="muted">Статус: {escape_html(status_label(article.publication_status))}</span>'
                '<div><button name="action" value="draft">Сохранить черновик</button> '
                '<button class="button-success" name="action" value="submit">Отправить на модерацию</button></div>'
                '</div></form>' + ''.join(detached_forms))
        if article_id != "new":
            body += self._delete_form(article.article_id)
            for note in self.db.list_entities(d.EditorRemark, 'article_id=?', (article.article_id,)):
                body += f'<article><strong>Замечание редактора:</strong> {escape_html(note.remark_text)}</article>'
        body += '<script src="/assets/editor.js"></script>'
        self.app.views[1].display_draft(article.content)
        return body

    def _moderation(self, data: dict[str, str] | None = None) -> str:
        selected = self.params.get("filter", "all")
        self.app.views[2].display_queue(selected)
        notices = {'published': 'Статья опубликована', 'returned': 'Возвращена на доработку',
                   'priority': 'Приоритет обновлён', 'confirmed': 'Жалоба подтверждена',
                   'dismissed': 'Жалоба отклонена'}
        notice = notices.get(self.params.get('result', ''), '')
        body = (f'<p role="status">{escape_html(notice)}</p>' if notice else '')
        body += '<nav class="filter-nav" aria-label="Разделы модерации">' + ''.join(
            f'<a href="/moderation?filter={value}" class="{"selected" if selected == value else ""}">{label}</a>'
            for value, label in (("all", "Всё"), ("articles", "Статьи"), ("complaints", "Жалобы"))
        ) + '</nav>'
        if selected in ("all", "articles"):
            tickets = self.db.list_entities(d.ModerationQueueEntry,
                                     'processed_at IS NULL AND article_id IN '
                                     '(SELECT article_id FROM Article WHERE deleted_at IS NULL)',
                                     order='priority DESC, received_at')
            rows = [(ticket, article) for ticket in tickets if (article := self.db.get(d.Article, ticket.article_id))]
            body += (f'<section class="prototype-panel queue-panel"><h2 id="queue-title">Очередь модерации '
                     f'<span class="heading-count">{len(rows)}</span></h2>')
            if not rows:
                body += '<p class="empty-state">Материалов на модерации нет.</p></section>'
            else:
                target = self.current_path.rsplit('/', 1)[-1] if data is not None else self.params.get('article')
                current_ticket, current_article = next(
                    (entry for entry in rows if target in (entry[0].queue_entry_id, entry[1].article_id)), rows[0])
                body += ('<div class="queue-scroll" tabindex="0" role="region" aria-labelledby="queue-title"><table class="queue-table">'
                         '<thead><tr><th scope="col">ID</th><th scope="col">Заголовок</th><th scope="col">Автор</th>'
                         '<th scope="col">Подразделение</th><th scope="col">Дата подачи</th><th scope="col">Статус</th></tr></thead><tbody>')
                for ticket, article in rows:
                    author = self.db.get(d.ContentAuthor, article.author_id)
                    active = current_article.article_id == article.article_id
                    url = escape_html('/moderation?' + urlencode({'filter': selected, 'article': article.article_id}))
                    selected_row = ' class="queue-selected"' if active else ''
                    selected_link = ' aria-current="true"' if active else ''
                    body += (f'<tr{selected_row}><td>{escape_html(ticket.queue_entry_id[:8])}</td>'
                             f'<td><a href="{url}"{selected_link}>{escape_html(article.title)}</a></td>'
                             f'<td>{escape_html(author.full_name if author else "Автор")}</td>'
                             f'<td>{escape_html(author.department if author and author.department else "—")}</td>'
                             f'<td>{escape_html(ticket.received_at.date())}</td>'
                             f'<td><span class="queue-status">{escape_html(status_label(article.publication_status))}</span></td></tr>')
                body += '</tbody></table></div></section>'
                article_id = escape_html(current_article.article_id)
                ticket_id = escape_html(current_ticket.queue_entry_id)
                author = self.db.get(d.ContentAuthor, current_article.author_id)
                category = self.db.get(d.Category, current_article.category_id)
                media = self.db.list_entities(d.MediaAttachment, 'article_id=?', (current_article.article_id,))
                files = ''.join(f'<li><a href="/media/{escape_html(item.media_id)}">{escape_html(item.file_url)}</a></li>' for item in media)
                note = data.get('note', '') if data and self.current_path.endswith('/' + current_article.article_id) else ''
                body += (f'<article id="review" class="prototype-panel review-panel management-card"><h2>Проверка статьи: '
                         f'{escape_html(current_article.title)}</h2>'
                         f'<p class="muted">Автор: {escape_html(author.full_name if author else "—")} · '
                         f'Рубрика: {escape_html(category.name if category else "—")} · '
                         f'Символов: {len(current_article.content)} · Вложений: {len(media)}</p>'
                         '<section class="review-preview"><h3>Предпросмотр статьи</h3>'
                         f'<div class="article-body">{render_markdown(current_article.content)}</div>'
                         + (f'<ul class="review-attachments">{files}</ul>' if files else '') +
                         f'<a href="/article/{article_id}">Открыть статью и вложения</a></section>'
                         f'<form class="review-priority" method="post" action="/moderation/priority/{ticket_id}">{self._csrf()}'
                         f'<label>Приоритет <input type="number" min="0" max="10" name="priority" value="{current_ticket.priority}"></label>'
                         '<button>Установить приоритет</button></form>'
                         f'<form class="review-decision" method="post" action="/moderation/article/{article_id}">{self._csrf()}'
                         f'<label>Замечание редактора<textarea name="note">{escape_html(note)}</textarea></label>'
                         '<div class="review-actions"><button class="button-reject" name="decision" value="reject">Вернуть на доработку</button>'
                         '<button class="button-success" name="decision" value="approve">Одобрить и опубликовать</button></div></form></article>')
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
                body += (f'<article class="list-card management-card"><p>{escape_html(comment.text)}</p><small>Жалоб: {count}; статус: {escape_html(status_label(comment.status))}</small>'
                         f'<form method="post" action="/moderation/complaint/{escape_html(comment_id)}">{self._csrf()}'
                         '<button name="decision" value="confirm">Подтвердить удаление</button> '
                         '<button name="decision" value="dismiss">Отклонить жалобу и восстановить</button></form></article>')
        body += '''<script>document.querySelectorAll('.management-card form').forEach(form => form.addEventListener('submit', () => { setTimeout(() => form.querySelectorAll('button').forEach(button => button.disabled = true), 0); }));</script>'''
        return body

    def _admin(self, data: dict[str, str] | None = None, error_path: str = "") -> str:
        notice = '<p role="status">Изменения сохранены.</p>' if self.params.get('result') == 'saved' else ''
        body = notice + '<nav class="filter-nav" aria-label="Разделы администрирования"><a href="#categories">Рубрики</a><a href="#users">Пользователи и роли</a><a href="#permissions">Права доступа</a><a href="#reports">Отчёты</a></nav><section id="categories"><h2>Рубрики</h2>'
        for rubric in self.db.list_entities(d.Category):
            values = data if data and error_path == '/admin/rubric' and data.get('id') == rubric.category_id else {}
            body += (f'<form method="post" action="/admin/rubric">{self._csrf()}'
                     f'<input type="hidden" name="id" value="{escape_html(rubric.category_id)}">'
                     f'<label>Название<input name="name" value="{escape_html(values.get("name", rubric.name))}" required></label> '
                     f'<label>Описание<input name="description" value="{escape_html(values.get("description", rubric.description))}"></label> '
                     '<button name="action" value="save">Сохранить</button> ')
            if not self.db.list_entities(d.Article, 'category_id=?', (rubric.category_id,)):
                body += '<button name="action" value="delete" onclick="return confirm(&quot;Удалить рубрику?&quot;)">Удалить</button>'
            body += '</form>'
        new_values = data if data and error_path == '/admin/rubric' and not data.get('id') else {}
        body += (f'<form method="post" action="/admin/rubric">{self._csrf()}'
                 f'<label>Новая рубрика<input name="name" value="{escape_html(new_values.get("name", ""))}" required></label>'
                 f'<label>Описание<input name="description" value="{escape_html(new_values.get("description", ""))}"></label>'
                 '<button name="action" value="save">Добавить</button></form>')
        roles = self.db.list_entities(d.Role)
        options = "".join(f'<option value="{escape_html(r.role_id)}">{escape_html(role_label(r.role_name))}</option>' for r in roles)
        body += '</section><section id="users"><h2>Пользователи и роли</h2><div class="table-scroll"><table><thead><tr><th>Логин</th><th>Текущая роль</th><th>Действие</th></tr></thead><tbody>'
        for account in self.db.list_entities(d.UserAccount):
            current_role = next((role_label(r.role_name) for r in roles if r.role_id == account.role_id), "Не назначена")
            body += (f'<tr><td>{escape_html(account.login)}</td><td>{escape_html(current_role)}</td><td>'
                     f'<form method="post" action="/admin/role">{self._csrf()}'
                     f'<input type="hidden" name="account" value="{escape_html(account.account_id)}">'
                     f'<label>Новая роль для {escape_html(account.login)}<select name="role">' + "".join(
                         f'<option value="{escape_html(r.role_id)}" {"selected" if r.role_id == account.role_id else ""}>{escape_html(role_label(r.role_name))}</option>'
                         for r in roles) + '</select></label><button onclick="return confirm(&quot;Изменить роль пользователя?&quot;)">Назначить роль</button></form></td></tr>')
        body += '</tbody></table></div></section><section id="permissions"><h2>Права доступа</h2>'
        for role_obj in roles:
            rights = self.db.list_entities(d.AccessPermission, 'role_id=?', (role_obj.role_id,))
            body += f'<p>{escape_html(role_label(role_obj.role_name))}: {escape_html(", ".join(r.operation_code for r in rights))}</p>'
            for right in rights:
                body += (f'<form method="post" action="/admin/permission" class="inline">{self._csrf()}'
                         f'<input type="hidden" name="role" value="{escape_html(role_obj.role_id)}">'
                         f'<input type="hidden" name="code" value="{escape_html(right.operation_code)}">'
                         f'<button onclick="return confirm(&quot;Удалить право доступа?&quot;)" name="action" value="remove">Убрать {escape_html(right.operation_code)}</button></form> ')
        body += (f'<form method="post" action="/admin/permission">{self._csrf()}'
                 f'<label>Роль<select name="role">{options}</select></label><label>Код операции<input name="code" value="{escape_html(data.get("code", "") if data and error_path == "/admin/permission" else "")}" required></label>'
                 '<button name="action" value="add">Добавить право</button></form>')
        body += (f'</section><section id="reports"><h2>Отчёты</h2><form method="post" action="/admin/report">{self._csrf()}'
                 '<label>Начало периода<input type="date" name="start" required></label>'
                 '<label>Конец периода<input type="date" name="end" required></label><button>Сформировать</button></form>')
        for report in self.reports.get_reports():
            body += (f'<p>{escape_html(report.period)}: публикаций {report.publication_count}, '
                     f'комментариев {report.comment_count}, реакций {report.reaction_count}, '
                     f'охват {report.reach_metric:g}</p>')
        return body + '</section>'

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
            tickets = self.db.list_entities(d.ModerationQueueEntry, 'article_id=? AND processed_at IS NULL', (article_id,))
            if not tickets:
                raise d.NotFound("Заявка отсутствует или уже обработана")
            if data.get("decision") == "approve":
                self.publications.publish_material(article_id, editor.editor_id)
            elif data.get("decision") == "reject":
                self.publications.return_for_revision(article_id, editor.editor_id, data.get("note", ""))
            else:
                raise d.DomainException("Неизвестное решение")
            return self._redirect("/moderation?filter=articles&result=" + ("published" if data.get("decision") == "approve" else "returned"))
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
            return self._redirect('/moderation?' + urlencode({
                'filter': 'articles', 'result': 'priority', 'article': article.article_id,
            }))
        if path.startswith("/moderation/complaint/"):
            self._require("article.moderate")
            decision = data.get("decision", "")
            if decision is None:
                raise d.DomainException("Неизвестное решение")
            self.moderation.apply_decision(decision, path.split("/")[3])
            return self._redirect("/moderation?filter=complaints&result=" + ("confirmed" if decision == "confirm" else "dismissed"))
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
        if data.get("action") == "submit" and not article.ready_for_moderation():
            raise d.DomainException("article_missing_required_fields")
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
        return self._redirect("/admin?result=saved")

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
