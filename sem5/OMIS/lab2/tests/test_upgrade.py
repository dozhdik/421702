import json

from omis_blog import domain as d
from omis_blog.auth import authenticate
from omis_blog.main import BlogPlatformApp
from omis_blog.storage import Database
from omis_blog.web import WebApp, render_markdown
from scripts.seed_demo import seed
from tests.test_web import Client


def test_registration_author_workflow_and_session_rotation(tmp_path):
    path = tmp_path / "new.sqlite"
    seed(str(path))
    app = BlogPlatformApp(path)
    app.initialize_system()
    web = WebApp(app)
    author = Client(web)
    assert 'Регистрация' in author.request("/")[1]
    old_cookie = author.cookie
    author.request("/register")
    status, _, headers = author.request("/register", {
        "full_name": "Анна Петрова", "login": "New.Author", "password": "a-long-password-2026",
        "confirmation": "a-long-password-2026", "role": "admin",
    })
    assert status.startswith("303") and headers["Location"] == "/my-articles"
    assert author.cookie != old_cookie
    assert "HttpOnly" in headers["Set-Cookie"] and "SameSite=Lax" in headers["Set-Cookie"]
    assert app.db.get(d.UserSession, old_cookie.removeprefix("sid=")) is None
    account = authenticate(app.db, "NEW.AUTHOR", "a-long-password-2026")
    assert account and account.login == "new.author"
    assert app.db.list_entities(d.ContentAuthor, 'user_id=?', (account.user_id,))
    assert app.db.list_entities(d.Reader, 'user_id=?', (account.user_id,))
    body = author.request("/my-articles")[1]
    assert "Написать статью" in body and "Модерация</a>" not in body
    assert author.request("/moderation")[0] == "403 Forbidden"
    assert author.request("/admin")[0] == "403 Forbidden"
    before = len(app.db.list_entities(d.UserAccount))
    assert author.request("/register", {"full_name": "Дубль", "login": "NEW.AUTHOR",
                                       "password": "another-password", "confirmation": "another-password"})[0] == "400 Bad Request"
    assert author.request("/register", {"full_name": "Короткий", "login": "short.user",
                                       "password": "short", "confirmation": "short"})[0] == "400 Bad Request"
    assert author.request("/register", {"full_name": "Ошибка", "login": "valid.user",
                                       "password": "another-password", "confirmation": "different-password"})[0] == "400 Bad Request"
    assert len(app.db.list_entities(d.UserAccount)) == before
    rubric = app.db.list_entities(d.Category)[0].category_id
    assert author.request("/article/save", {"title": "Мой материал", "content": "Полный текст",
                                           "rubric": rubric, "tags": "команда", "action": "draft"})[0].startswith("303")
    article = app.db.list_entities(d.Article, 'title=?', ("Мой материал",))[0]
    assert article.author_id == app.db.list_entities(d.ContentAuthor, 'user_id=?', (account.user_id,))[0].author_id
    assert "Мой материал" in author.request("/my-articles")[1]
    assert "Полный текст" in author.request("/editor/" + article.article_id)[1]
    other = Client(web)
    other.login("author")
    assert other.request("/editor/" + article.article_id)[0] == "403 Forbidden"
    assert other.request("/article/save", {"id": article.article_id, "title": "Wrong", "action": "submit"})[0] == "403 Forbidden"
    assert author.request("/article/save", {"id": article.article_id, "title": "Мой материал",
                                           "content": "Полный текст", "rubric": rubric,
                                           "action": "submit"})[0].startswith("303")
    assert "На модерации" in author.request("/my-articles")[1]
    editor = Client(web)
    editor.login("editor")
    assert editor.request("/moderation/article/" + article.article_id,
                          {"decision": "reject", "note": "Уточните источник"})[0].startswith("303")
    author.request("/logout", {})
    author.request("/login")
    assert author.request("/login", {"login": "new.author", "password": "a-long-password-2026"})[0].startswith("303")
    body = author.request("/my-articles")[1]
    assert "Требует правок" in body and "Уточните источник" in body
    reopened = Database(path)
    assert reopened.get(d.Article, article.article_id).publication_status == d.ArticleStatus.NEEDS_REVISION


def test_seed_five_complete_articles_and_preserves_edits(tmp_path):
    path = tmp_path / "seed.sqlite"
    seed(str(path))
    db = Database(path)
    items = json.load(open("задание/seed_articles.json", encoding="utf-8"))
    seeded = db.list_entities(d.Article, "seed_key <> ''")
    assert len(seeded) == len(items) == 5
    app = BlogPlatformApp(path)
    app.initialize_system()
    visitor = Client(WebApp(app))
    feed_html = visitor.request("/")[1]
    assert all(item["title"] in feed_html for item in items)
    assert visitor.request("/article/" + seeded[0].article_id)[0] == "200 OK"
    for item in items:
        article = next(article for article in seeded if article.seed_key == item["seed_key"])
        assert article.content == item["content_markdown"]
        assert article.summary == item["summary"]
        assert article.publication_status == d.ArticleStatus.PUBLISHED
        assert db.get(d.SearchIndex, db.list_entities(d.SearchIndex, 'article_id=?', (article.article_id,))[0].index_id)
        assert db.list_entities(d.PublicationRecord, 'article_id=?', (article.article_id,))
        assert {tag.keyword for tag in db.get_article_tags(article.article_id)} == set(item["tags"])
    first = seeded[0]
    first.title = "Отредактировано локально"
    db.save(first)
    db.close()
    seed(str(path))
    db = Database(path)
    assert len(db.list_entities(d.Article, "seed_key <> ''")) == 5
    assert db.get(d.Article, first.article_id).title == "Отредактировано локально"
    names = [row[0] for row in db.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    assert all(name.isascii() for name in names)
    assert db.connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert not db.connection.execute("PRAGMA foreign_key_check").fetchall()


def test_markdown_escapes_user_html():
    rendered = render_markdown("# Заголовок\n\nТекст <script>alert(1)</script>\n\n## Раздел")
    assert "<h2>Заголовок</h2>" in rendered
    assert "&lt;script&gt;" in rendered
    assert "<script>" not in rendered
