"""Idempotent local demo content. Run: python3 -m scripts.seed_demo --db blog.sqlite."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from omis_blog import domain as d
from omis_blog.auth import hash_password
from omis_blog.main import BlogPlatformApp


def id_for(value: str) -> str:
    return str(uuid5(NAMESPACE_URL, "omis-blog-demo:" + value))


def seed(db_path: str) -> None:
    app = BlogPlatformApp(db_path)
    app.initialize_system()
    db = app.db
    initialize_rights = db.connection.execute(
        "SELECT 1 FROM setting WHERE key='demo_rights_initialized_v2'").fetchone() is None
    reader_rights = ["feed.read", "comment.write", "reaction.write"]
    roles = {
        "author": ("Автор", ["article.write", *reader_rights]),
        "editor": ("Редактор", ["article.moderate", *reader_rights]),
        "reader": ("Читатель", reader_rights),
        "admin": ("Администратор", ["admin", *reader_rights]),
    }
    for login, (name, rights) in roles.items():
        role_id = id_for("role:" + login)
        user_id = id_for("user:" + login)
        account_id = id_for("account:" + login)
        password_hash = hash_password(login + "123", "00" * 16)
        if not db.get(d.Role, role_id):
            db.save(d.Role(role_id=role_id, role_name=name, description=name))
        if initialize_rights:
            for right in rights:
                permission = d.AccessPermission(permission_id=id_for(login + ":" + right),
                                                 operation_code=right, role_id=role_id)
                if not db.get(d.AccessPermission, permission.permission_id):
                    db.save(permission)
        if not db.get(d.User, user_id):
            db.save(d.User(user_id=user_id, full_name=name + " Демо",
                           password_hash=password_hash, account_id=account_id))
        if not db.get(d.UserAccount, account_id):
            db.save(d.UserAccount(account_id=account_id, login=login,
                                  password_hash=password_hash, user_id=user_id, role_id=role_id))
        reader_id = id_for("reader:" + login)
        if not db.get(d.Reader, reader_id):
            db.save(d.Reader(reader_id=reader_id, full_name=name + " Демо",
                             job_title=name, user_id=user_id))
    author = d.ContentAuthor(author_id=id_for("author"), full_name="Автор Демо", department="Маркетинг",
                             user_id=id_for("user:author"))
    editor = d.Editor(editor_id=id_for("editor"), full_name="Редактор Демо", section="Новости",
                        user_id=id_for("user:editor"))
    admin = d.PlatformAdministrator(administrator_id=id_for("admin"), full_name="Администратор Демо",
                                     access_level="Полный", user_id=id_for("user:admin"))
    for profile in (author, editor, admin):
        model = type(profile)
        if not db.get(model, getattr(profile, next(iter(model.__dataclass_fields__)))):
            db.save(profile)
    if initialize_rights:
        db.connection.execute("INSERT INTO setting(key,value) VALUES ('demo_rights_initialized_v2','1')")
        db.connection.commit()
    rubric = d.Category(category_id=id_for("rubric:news"), name="Новости компании",
                       description="Внутренние новости", administrator_id=admin.administrator_id)
    if not db.get(d.Category, rubric.category_id):
        db.save(rubric)
    tag = d.Tag(tag_id=id_for("tag:news"), keyword="новости")
    if not db.get(d.Tag, tag.tag_id):
        db.save(tag)
    published = d.Article(article_id=id_for("article:published"), title="Добро пожаловать",
                         content="Корпоративная платформа открыта для сотрудников.",
                         author_id=author.author_id, category_id=rubric.category_id)
    draft = d.Article(article_id=id_for("article:draft"), title="Черновик",
                     author_id=author.author_id)
    pending = d.Article(article_id=id_for("article:pending"), title="Новости отдела",
                       content="Отдел представил новые материалы.", author_id=author.author_id,
                       category_id=rubric.category_id)
    new_articles: set[str] = set()
    for article in (published, draft, pending):
        if db.get(d.Article, article.article_id) is None:
            db.save(article)
            new_articles.add(article.article_id)
    if published.article_id in new_articles:
        db.set_article_tags(published.article_id, [tag])
    publication = app.controllers[0]
    current_published = db.get(d.Article, published.article_id)
    if published.article_id in new_articles and current_published and current_published.publication_status == d.ArticleStatus.DRAFT:
        publication.process_submission(published)
        publication.publish_material(published.article_id, editor.editor_id)
    current_pending = db.get(d.Article, pending.article_id)
    if pending.article_id in new_articles and current_pending and current_pending.publication_status == d.ArticleStatus.DRAFT:
        publication.process_submission(pending)
    reader = db.get(d.Reader, id_for("reader:reader"))
    assert reader
    first = d.Comment(comment_id=id_for("comment:1"), text="Рады запуску!",
                          article_id=published.article_id, reader_id=reader.reader_id)
    reply = d.Comment(comment_id=id_for("comment:2"), text="Спасибо!",
                          article_id=published.article_id, reader_id=id_for("reader:author"),
                          parent_id=first.comment_id, replied_at=d.utc_now())
    for comment in (first, reply):
        if not db.get(d.Comment, comment.comment_id):
            db.save(comment)
    reaction_id = id_for("reaction:1")
    if not db.get(d.Reaction, reaction_id):
        db.save(d.Reaction(reaction_id=reaction_id, article_id=published.article_id,
                           reader_id=reader.reader_id))
    for login in ("author", "editor"):
        complaint = d.Complaint(complaint_id=id_for("complaint:" + login), reason="Проверить содержание",
                             comment_id=first.comment_id, reader_id=id_for("reader:" + login))
        if not db.get(d.Complaint, complaint.complaint_id):
            db.save(complaint)
    entries = json.loads((Path(__file__).resolve().parent.parent / "задание" / "seed_articles.json").read_text(encoding="utf-8"))
    for item in entries:
        key = item["seed_key"]
        article_id = id_for("article:" + key)
        if db.get(d.Article, article_id) or db.list_entities(d.Article, 'seed_key=?', (key,)):
            continue
        categories = db.list_entities(d.Category, 'name=?', (item["category"],))
        category = categories[0] if categories else d.Category(
            category_id=id_for("category:" + item["category"]), name=item["category"],
            administrator_id=admin.administrator_id)
        if not categories:
            db.save(category)
        tags = []
        for keyword in item["tags"]:
            found = db.list_entities(d.Tag, 'keyword=?', (keyword,))
            tag_item = found[0] if found else d.Tag(tag_id=id_for("tag:" + keyword), keyword=keyword)
            if not found:
                db.save(tag_item)
            tags.append(tag_item)
        article = d.Article(article_id=article_id, title=item["title"],
                            content=item["content_markdown"], summary=item["summary"],
                            cover_theme=item["cover_theme"], seed_key=key,
                            author_id=author.author_id, category_id=category.category_id,
                            classified_at=d.utc_now())
        db.save(article)
        db.set_article_tags(article_id, tags)
        publication.process_submission(article)
        publication.publish_material(article_id, editor.editor_id)
        published_article = db.get(d.Article, article_id)
        assert published_article is not None
        published_article.published_at = datetime.fromisoformat(item["published_at"])
        db.save(published_article)
    app.stop_application()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="blog.sqlite")
    seed(parser.parse_args().db)
