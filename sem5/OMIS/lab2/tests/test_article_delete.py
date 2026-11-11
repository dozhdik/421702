import pytest

from omis_blog import domain as d
from omis_blog.main import BlogPlatformApp
from omis_blog.storage import ArticleRepository, Database
from omis_blog.web import WebApp
from scripts.seed_demo import id_for, seed
from tests.test_web import Client


@pytest.mark.parametrize("status", list(d.ArticleStatus))
def test_author_soft_delete_in_every_status(tmp_path, status):
    path = tmp_path / "articles.sqlite"
    seed(str(path))
    app = BlogPlatformApp(path)
    app.initialize_system()
    article = d.Article(title="Удаляемая статья", content="Полный текст для поиска",
                        publication_status=status, author_id=id_for("author"),
                        category_id=id_for("rubric:news"))
    app.db.save(article)
    app.db.save(d.SearchIndex(article_id=article.article_id,
                              lexemes="удаляемая статья полный текст для поиска"))
    ticket = None
    if status == d.ArticleStatus.IN_MODERATION:
        ticket = d.ModerationQueueEntry(article_id=article.article_id)
        app.db.save(ticket)
    author = Client(WebApp(app))
    author.login("author")
    dashboard = author.request("/my-articles")[1]
    assert "Удаляемая статья" in dashboard
    assert f'/article/{article.article_id}/delete' in dashboard
    if status in (d.ArticleStatus.DRAFT, d.ArticleStatus.NEEDS_REVISION):
        editor_html = author.request("/editor/" + article.article_id)[1]
        assert 'onsubmit="return confirm(' in editor_html
        assert f'/article/{article.article_id}/delete' in editor_html
    saved_csrf = author.csrf
    author.csrf = "invalid"
    assert author.request(f"/article/{article.article_id}/delete", {})[0] == "403 Forbidden"
    author.csrf = saved_csrf
    assert app.db.get(d.Article, article.article_id).deleted_at is None
    response, _, headers = author.request(f"/article/{article.article_id}/delete", {})
    assert response.startswith("303") and headers["Location"] == "/my-articles"
    stored = app.db.get(d.Article, article.article_id)
    assert stored and stored.deleted_at is not None
    assert stored.deleted_by == id_for("user:author")
    assert stored.publication_status == status
    assert "Удаляемая статья" not in author.request("/my-articles")[1]
    assert "Удаляемая статья" not in author.request("/")[1]
    assert "Удаляемая статья" not in author.request("/?q=удаляемая")[1]
    assert author.request("/article/" + article.article_id)[0] == "404 Not Found"
    assert author.request("/editor/" + article.article_id)[0] == "404 Not Found"
    assert author.request("/article/save", {"id": article.article_id, "title": "Восстановить",
                                            "action": "draft"})[0] == "404 Not Found"
    if ticket:
        assert app.db.get(d.ModerationQueueEntry, ticket.queue_entry_id).processed_at is not None
        moderator = Client(author.web)
        moderator.login("editor")
        assert "Удаляемая статья" not in moderator.request("/moderation")[1]
        assert moderator.request("/moderation/article/" + article.article_id,
                                 {"decision": "approve"})[0] == "404 Not Found"
    app.stop_application()
    reopened = Database(path)
    assert reopened.get(d.Article, article.article_id).deleted_at is not None
    assert reopened.list_entities(d.SearchIndex, 'article_id=?', (article.article_id,))
    reopened.close()


def test_foreign_delete_requires_separate_permission(tmp_path):
    path = tmp_path / "rights.sqlite"
    seed(str(path))
    app = BlogPlatformApp(path)
    app.initialize_system()
    article = app.db.get(d.Article, id_for("article:published"))
    assert article is not None
    web = WebApp(app)
    reader = Client(web)
    reader.login("reader")
    assert reader.request(f"/article/{article.article_id}/delete", {})[0] == "403 Forbidden"
    editor = Client(web)
    editor.login("editor")
    assert editor.request(f"/article/{article.article_id}/delete", {})[0] == "403 Forbidden"
    admin = Client(web)
    admin.login("admin")
    assert admin.request(f"/article/{article.article_id}/delete", {})[0] == "403 Forbidden"
    app.db.save(d.AccessPermission(operation_code="article.delete.any", role_id=id_for("role:admin")))
    assert "Удалить" in admin.request("/article/" + article.article_id)[1]
    assert admin.request(f"/article/{article.article_id}/delete", {})[0].startswith("303")
    assert app.db.get(d.Article, article.article_id).deleted_by == id_for("user:admin")


def test_deletion_keeps_related_data_and_seed_does_not_restore(tmp_path):
    path = tmp_path / "history.sqlite"
    seed(str(path))
    app = BlogPlatformApp(path)
    app.initialize_system()
    article_id = id_for("article:published")
    comment = app.db.list_entities(d.Comment, 'article_id=?', (article_id,))[0]
    app.db.save(d.Complaint(reason="Проверить", comment_id=comment.comment_id,
                            reader_id=id_for("reader:admin")))
    assert app.controllers[1].complaint_repository.get_complaint_queue()
    related = {model: len(app.db.list_entities(model, 'article_id=?', (article_id,)))
               for model in (d.Comment, d.Reaction, d.PublicationRecord)}
    complaints = len(app.db.list_entities(d.Complaint, 'comment_id=?', (comment.comment_id,)))
    author = Client(WebApp(app))
    author.login("author")
    assert author.request(f"/article/{article_id}/delete", {})[0].startswith("303")
    assert not app.controllers[1].complaint_repository.get_complaint_queue()
    app.stop_application()
    seed(str(path))
    db = Database(path)
    assert db.get(d.Article, article_id).deleted_at is not None
    with pytest.raises(d.DomainException, match="article_deleted"):
        db.save(db.get(d.Article, article_id))
    assert all(len(db.list_entities(model, 'article_id=?', (article_id,))) == count
               for model, count in related.items())
    assert len(db.list_entities(d.Complaint, 'comment_id=?', (comment.comment_id,))) == complaints
    assert db.connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert not db.connection.execute("PRAGMA foreign_key_check").fetchall()
    extra = d.Article(title="Дополнительная статья", author_id=id_for("author"))
    db.save(extra)
    ArticleRepository(db).delete(extra.article_id)
    assert db.get(d.Article, extra.article_id).deleted_at is not None
