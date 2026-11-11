import io
import re
from urllib.parse import urlencode

from omis_blog import domain as d
from omis_blog.auth import hash_password
from omis_blog.main import BlogPlatformApp
from omis_blog.web import WebApp
from scripts.seed_demo import id_for, seed


class Client:
    def __init__(self, web):
        self.web = web
        self.cookie = ""
        self.csrf = ""

    def request(self, path, data=None, files=None):
        if data is None:
            raw = b""
            method = "GET"
            content_type = "application/x-www-form-urlencoded"
        elif files:
            boundary = "omis-test-boundary"
            chunks = []
            for key, value in {**data, "csrf": self.csrf}.items():
                chunks.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n").encode())
            for name, filename, payload, mime in files:
                chunks.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; filename=\"{filename}\"\r\n"
                               f"Content-Type: {mime}\r\n\r\n").encode() + payload + b"\r\n")
            raw = b"".join(chunks) + f"--{boundary}--\r\n".encode()
            method = "POST"
            content_type = f"multipart/form-data; boundary={boundary}"
        else:
            raw = urlencode({**data, "csrf": self.csrf}).encode()
            method = "POST"
            content_type = "application/x-www-form-urlencoded"
        path, _, query = path.partition("?")
        response = {}

        def start(status, headers):
            response["status"] = status
            response["headers"] = dict(headers)

        body = b"".join(self.web({
            "REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query,
            "CONTENT_LENGTH": str(len(raw)), "CONTENT_TYPE": content_type,
            "HTTP_COOKIE": self.cookie, "wsgi.input": io.BytesIO(raw),
        }, start)).decode("utf-8", "replace")
        if "Set-Cookie" in response["headers"]:
            self.cookie = response["headers"]["Set-Cookie"].split(";", 1)[0]
        token = re.search(r'name="csrf" value="([^"]+)"', body)
        if token:
            self.csrf = token.group(1)
        return response["status"], body, response["headers"]

    def login(self, name):
        self.request("/login")
        status, _, _ = self.request("/login", {"login": name, "password": name + "123"})
        assert status.startswith("303")
        self.request("/")


def test_role_scenarios_in_browser(tmp_path):
    path = tmp_path / "demo.sqlite"
    seed(str(path))
    app = BlogPlatformApp(path)
    app.initialize_system()
    web = WebApp(app)
    author = Client(web)
    author.login("author")
    saved_csrf = author.csrf
    author.csrf = "invalid"
    assert author.request("/article/save", {"title": "Подмена", "action": "draft"})[0] == "403 Forbidden"
    author.csrf = saved_csrf
    status, body, _ = author.request("/editor/new")
    assert status == "200 OK" and "Сохранить черновик" in body
    rubric = id_for("rubric:news")
    status, _, _ = author.request("/article/save", {
        "title": "Тестовая публикация", "content": "Проверка полного цикла", "rubric": rubric,
        "tags": "тест", "font": "system", "preview": "on", "action": "draft",
    })
    assert status.startswith("303")
    new_article = app.db.list_entities(d.Article, 'title=?', ("Тестовая публикация",))[0]
    author.request("/editor/" + new_article.article_id)
    status, _, _ = author.request("/article/save", {
        "id": new_article.article_id, "title": "Тестовая публикация", "content": "Проверка полного цикла",
        "rubric": rubric, "tags": "тест", "action": "submit",
    })
    assert status.startswith("303")
    assert app.db.get(d.Article, new_article.article_id).publication_status == d.ArticleStatus.IN_MODERATION
    other_user = d.User(full_name="Другой автор")
    other_account = d.UserAccount(login="other", password_hash=hash_password("other123"),
                                     user_id=other_user.user_id, role_id=id_for("role:author"))
    other_user.account_id = other_account.account_id
    other_user.password_hash = other_account.password_hash
    app.db.save(other_user)
    app.db.save(other_account)
    app.db.save(d.ContentAuthor(full_name="Другой автор", user_id=other_user.user_id))
    other = Client(web)
    other.login("other")
    assert other.request("/editor/" + new_article.article_id)[0] == "403 Forbidden"
    assert other.request("/article/save", {"id": new_article.article_id, "title": "Взлом",
                                           "action": "draft"})[0] == "403 Forbidden"
    reader = Client(web)
    reader.login("reader")
    author.request("/?page=2")
    author_session_id = author.cookie.split("=", 1)[1]
    reader.request("/")
    assert web.ui_states[author_session_id].feed.current_page == 2
    assert reader.request("/article/" + new_article.article_id)[0] == "403 Forbidden"
    assert reader.request("/moderation")[0] == "403 Forbidden"
    assert reader.request("/editor/" + new_article.article_id)[0] == "403 Forbidden"
    editor = Client(web)
    editor.login("editor")
    status, body, _ = editor.request("/moderation")
    assert status == "200 OK" and "Тестовая публикация" in body
    status, _, _ = editor.request("/moderation/article/" + new_article.article_id,
                                  {"decision": "approve"})
    assert status.startswith("303")
    status, body, _ = reader.request("/")
    assert "Тестовая публикация" in body
    status, body, _ = reader.request("/article/" + new_article.article_id)
    assert "Проверка полного цикла" in body
    status, _, _ = reader.request("/article/" + new_article.article_id + "/comment",
                                  {"text": "Хорошая новость"})
    assert status.startswith("303")
    status, body, _ = reader.request("/article/" + new_article.article_id)
    assert "Хорошая новость" in body
    comment = app.db.list_entities(d.Comment, 'article_id=?', (new_article.article_id,))[0]
    assert reader.request("/article/" + new_article.article_id + "/comment",
                          {"text": "Ответ в ветке", "parent": comment.comment_id})[0].startswith("303")
    reply = app.db.list_entities(d.Comment, 'text=?', ("Ответ в ветке",))[0]
    assert reply.parent_id == comment.comment_id
    status, _, _ = reader.request("/article/" + new_article.article_id + "/react",
                                      {"type": "like"})
    assert status.startswith("303")
    admin = Client(web)
    admin.login("admin")
    assert admin.request("/admin/rubric", {"name": "События", "action": "save"})[0].startswith("303")
    rubric_obj = app.db.list_entities(d.Category, 'name=?', ("События",))[0]
    assert admin.request("/admin/rubric", {"id": rubric_obj.category_id, "name": "События года",
                                            "action": "save"})[0].startswith("303")
    assert app.db.get(d.Category, rubric_obj.category_id).name == "События года"
    assert admin.request("/admin/rubric", {"id": rubric_obj.category_id,
                                            "action": "delete"})[0].startswith("303")
    assert app.db.get(d.Category, rubric_obj.category_id) is None
    assert admin.request("/admin/report", {"start": "2000-01-01", "end": "2100-01-01"})[0].startswith("303")
    assert "публикаций" in admin.request("/admin")[1]
    assert reader.request("/logout", {})[0].startswith("303")
    assert reader.request("/moderation")[0] == "403 Forbidden"
    app.stop_application()


def test_editor_media_autosave_search_archive_and_moderation(tmp_path):
    path = tmp_path / "demo.sqlite"
    seed(str(path))
    app = BlogPlatformApp(path)
    app.initialize_system()
    web = WebApp(app)
    author = Client(web)
    author.login("author")
    assert "setInterval" in author.request("/editor/new")[1]
    status, _, headers = author.request("/article/save", {"title": "Новый автосохранённый",
                                                        "content": "Начало", "action": "autosave"})
    assert status == "200 OK"
    assert app.db.get(d.Article, headers["X-Article-ID"]).title == "Новый автосохранённый"
    draft_id = id_for("article:draft")
    author.request("/editor/" + draft_id)
    rubric = id_for("rubric:news")
    values = {"id": draft_id, "title": "Автосохранённая новость", "content": "Текст после автосохранения",
              "rubric": rubric, "tags": "автотест", "font": "serif", "preview": "on", "action": "autosave"}
    status, body, _ = author.request("/article/save", values)
    assert status == "200 OK" and body == "Автосохранено"
    assert app.db.get(d.Article, draft_id).content == values["content"]
    assert web.ui.autosaved_at is not None
    values["action"] = "draft"
    assert author.request("/article/save", values,
                          [("media", "bad.png", b"not-an-image", "image/png")])[0] == "400 Bad Request"
    assert not app.db.list_entities(d.MediaAttachment, 'article_id=?', (draft_id,))
    status, _, _ = author.request("/article/save", values,
                                  [("media", "photo.png", b"\x89PNG\r\n\x1a\nimage", "image/png")])
    assert status.startswith("303")
    media = app.db.list_entities(d.MediaAttachment, 'article_id=?', (draft_id,))[0]
    assert app.db.get(d.Article, draft_id).formatting_id
    assert author.request("/media/" + media.media_id)[0] == "200 OK"
    reader = Client(web)
    reader.login("reader")
    assert reader.request("/media/" + media.media_id)[0] == "403 Forbidden"
    assert reader.request("/editor/" + draft_id)[0] == "403 Forbidden"
    author.request("/editor/" + draft_id)
    assert author.request("/media/" + media.media_id + "/delete", {})[0].startswith("303")
    assert app.db.get(d.MediaAttachment, media.media_id) is None
    author.request("/editor/" + draft_id)
    values["action"] = "submit"
    values.pop("preview")
    assert author.request("/article/save", values)[0].startswith("303")
    editor = Client(web)
    editor.login("editor")
    ticket = app.db.list_entities(d.ModerationQueueEntry, 'article_id=? AND processed_at IS NULL', (draft_id,))[0]
    assert editor.request("/moderation/priority/" + ticket.queue_entry_id, {"priority": "8"})[0].startswith("303")
    assert app.db.get(d.ModerationQueueEntry, ticket.queue_entry_id).priority == 8
    assert editor.request("/moderation/article/" + draft_id, {"decision": "approve"})[0].startswith("303")
    assert "font-family:serif" in reader.request("/article/" + draft_id)[1]
    for query in ("q=Автосохранённая", "author=Автор", "rubric=" + rubric, "tag=автотест"):
        assert "Автосохранённая новость" in reader.request("/?" + query)[1]
    assert "Текст после автосохранения" not in reader.request("/")[1]
    assert editor.request("/article/" + draft_id + "/status", {"status": "archived"})[0].startswith("303")
    assert "Автосохранённая новость" not in reader.request("/")[1]
    assert reader.request("/article/" + draft_id)[0] == "403 Forbidden"
    assert editor.request("/article/" + draft_id + "/status", {"status": "published"})[0].startswith("303")
    assert reader.request("/article/" + draft_id)[0] == "200 OK"
    assert editor.request("/article/" + draft_id + "/status", {"status": "unpublished"})[0].startswith("303")
    assert reader.request("/article/" + draft_id)[0] == "403 Forbidden"
    assert editor.request("/article/" + draft_id + "/status", {"status": "published"})[0].startswith("303")
    app.stop_application()


def test_third_complaint_and_admin_rights(tmp_path):
    path = tmp_path / "demo.sqlite"
    seed(str(path))
    app = BlogPlatformApp(path)
    app.initialize_system()
    web = WebApp(app)
    reader = Client(web)
    reader.login("reader")
    article_id = id_for("article:published")
    comment_id = id_for("comment:1")
    assert reader.request("/article/" + article_id + "/report",
                          {"comment": comment_id, "reason": "Проверить"})[0].startswith("303")
    assert "Рады запуску!" not in reader.request("/article/" + article_id)[1]
    editor = Client(web)
    editor.login("editor")
    assert "Проверить" not in editor.request("/moderation")[1]  # тикет показывает комментарий и число жалоб
    assert editor.request("/moderation/complaint/" + comment_id,
                          {"decision": "dismiss"})[0].startswith("303")
    assert "Рады запуску!" in reader.request("/article/" + article_id)[1]
    admin = Client(web)
    admin.login("admin")
    assert admin.request("/admin/permission", {"role": id_for("role:reader"),
                                                "code": "article.write", "action": "add"})[0].startswith("303")
    assert len(app.db.list_entities(d.AccessPermission, 'role_id=? AND operation_code=?',
                             (id_for("role:reader"), "article.write"))) == 1
    assert reader.request("/editor/new")[0] == "200 OK"
    assert admin.request("/admin/role", {"account": id_for("account:reader"),
                                          "role": id_for("role:reader")})[0].startswith("303")
    app.stop_application()
