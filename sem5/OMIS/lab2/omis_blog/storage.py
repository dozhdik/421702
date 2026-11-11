"""SQLite persistence and the four required UML repositories."""

from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from dataclasses import fields
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Generic, TypeVar, cast, get_args, get_type_hints

from omis_blog import domain as d


T = TypeVar("T")

ENTITIES = (
    d.User, d.UserAccount, d.Role, d.AccessPermission,
    d.ContentAuthor, d.Editor, d.Reader, d.PlatformAdministrator,
    d.Article, d.Category, d.Tag, d.MediaAttachment, d.FormattingOptions,
    d.ModerationQueueEntry, d.EditorRemark, d.PublicationRecord,
    d.Comment, d.Complaint, d.Reaction, d.SearchIndex,
    d.ActivityReport, d.UserSession,
)

EXCLUDED_FIELDS: dict[type, set[str]] = {d.User: {"password_hash"}}
UNIQUE_FIELDS: dict[type, tuple[str, ...]] = {
    d.UserAccount: ("login", "user_id"),
    d.ContentAuthor: ("user_id",),
    d.Editor: ("user_id",),
    d.Reader: ("user_id",),
    d.PlatformAdministrator: ("user_id",),
    d.FormattingOptions: ("article_id",),
    d.SearchIndex: ("article_id",),
    d.UserSession: ("authorization_token",),
    d.Complaint: ("comment_id", "reader_id"),
}

RELATIONSHIPS: dict[type, dict[str, type]] = {
    d.UserAccount: {"user_id": d.User, "role_id": d.Role},
    d.AccessPermission: {"role_id": d.Role},
    d.ContentAuthor: {"user_id": d.User},
    d.Editor: {"user_id": d.User},
    d.Reader: {"user_id": d.User},
    d.PlatformAdministrator: {"user_id": d.User},
    d.Article: {"author_id": d.ContentAuthor, "editor_id": d.Editor,
               "category_id": d.Category, "formatting_id": d.FormattingOptions,
               "deleted_by": d.User},
    d.Category: {"administrator_id": d.PlatformAdministrator},
    d.MediaAttachment: {"article_id": d.Article},
    d.FormattingOptions: {"article_id": d.Article},
    d.ModerationQueueEntry: {"article_id": d.Article, "editor_id": d.Editor},
    d.EditorRemark: {"article_id": d.Article, "editor_id": d.Editor},
    d.PublicationRecord: {"article_id": d.Article, "editor_id": d.Editor},
    d.Comment: {"article_id": d.Article, "reader_id": d.Reader,
                    "parent_id": d.Comment},
    d.Complaint: {"comment_id": d.Comment, "reader_id": d.Reader},
    d.Reaction: {"article_id": d.Article, "reader_id": d.Reader},
    d.SearchIndex: {"article_id": d.Article},
    d.ActivityReport: {"administrator_id": d.PlatformAdministrator},
    d.UserSession: {"user_id": d.User},
}


def _sql_type(component_type: Any) -> str:
    if component_type in (int, bool):
        return "INTEGER"
    if component_type is float:
        return "REAL"
    return "TEXT"


def _field_type(component_type: Any) -> Any:
    args = get_args(component_type)
    if args and type(None) in args:
        return next(x for x in args if x is not type(None))
    return component_type


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise d.DomainException("timestamp_requires_timezone")
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, StrEnum):
        return str(value)
    if isinstance(value, bool):
        return int(value)
    return value


class Database:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        existing_names = [row[0] for row in self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")]
        legacy_names = [name for name in existing_names if not name.isascii()]
        for table_name in existing_names:
            quoted_name = '"' + table_name.replace('"', '""') + '"'
            legacy_names.extend(row[1] for row in self.connection.execute(
                f'PRAGMA table_info({quoted_name})') if not row[1].isascii())
        if legacy_names:
            self.connection.close()
            raise RuntimeError("Legacy schema detected; run python3 -m scripts.migrate_legacy_db --db PATH")
        self.create_schema()

    def create_schema(self) -> None:
        for model_class in ENTITIES:
            hints = get_type_hints(model_class)
            columns = []
            for index, field_info in enumerate(fields(model_class)):
                if field_info.name in EXCLUDED_FIELDS.get(model_class, set()):
                    continue
                suffix = " PRIMARY KEY" if index == 0 else ""
                reference = RELATIONSHIPS.get(model_class, {}).get(field_info.name)
                if reference is not None:
                    target = fields(reference)[0].name
                    suffix += f' REFERENCES "{reference.__name__}"("{target}")'
                columns.append(f'"{field_info.name}" {_sql_type(_field_type(hints[field_info.name]))}{suffix}')
            if model_class is d.Complaint:
                columns.append('UNIQUE("comment_id", "reader_id")')
            elif model_class is d.Reaction:
                columns.append('UNIQUE("article_id", "reader_id")')
            else:
                for name in UNIQUE_FIELDS.get(model_class, ()):
                    columns.append(f'UNIQUE("{name}")')
            self.connection.execute(f'CREATE TABLE IF NOT EXISTS "{model_class.__name__}" ({", ".join(columns)})')
        self.connection.executescript("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_user_account ON User(account_id)
                WHERE account_id <> '';
            CREATE TABLE IF NOT EXISTS article_tag (
                article_id TEXT NOT NULL REFERENCES Article(article_id),
                tag_id TEXT NOT NULL REFERENCES Tag(tag_id),
                tagged_at TEXT NOT NULL,
                PRIMARY KEY (article_id, tag_id)
            );
            CREATE TABLE IF NOT EXISTS notification (
                id TEXT PRIMARY KEY, recipient TEXT NOT NULL,
                text TEXT NOT NULL, created_at TEXT NOT NULL, is_read INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS article_view (
                id TEXT PRIMARY KEY, article_id TEXT NOT NULL REFERENCES Article(article_id),
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS setting (
                key TEXT PRIMARY KEY, value TEXT NOT NULL
            );
        """)
        existing = {row[1] for row in self.connection.execute('PRAGMA table_info("Article")')}
        for name in ("summary", "cover_theme", "seed_key"):
            if name not in existing:
                self.connection.execute(f'ALTER TABLE "Article" ADD COLUMN "{name}" TEXT NOT NULL DEFAULT \'\'')
        if "deleted_at" not in existing:
            self.connection.execute('ALTER TABLE "Article" ADD COLUMN "deleted_at" TEXT')
        if "deleted_by" not in existing:
            self.connection.execute('ALTER TABLE "Article" ADD COLUMN "deleted_by" TEXT REFERENCES "User"("user_id")')
        self.connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_article_seed_key ON Article(seed_key) WHERE seed_key <> ''")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_article_visible_status ON Article(publication_status, published_at) WHERE deleted_at IS NULL")
        self.connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_account_login_casefold ON UserAccount(lower(login))")
        self.connection.commit()

    def save(self, entity: Any, *, commit: bool = True) -> None:
        model_class = type(entity)
        if model_class not in ENTITIES:
            raise TypeError(model_class)
        if model_class is d.Article:
            existing = self.connection.execute(
                'SELECT deleted_at FROM Article WHERE article_id=?', (entity.article_id,)).fetchone()
            if existing and existing[0] is not None:
                raise d.DomainException("article_deleted")
        data = {}
        for f in fields(entity):
            if f.name in EXCLUDED_FIELDS.get(model_class, set()):
                continue
            value = getattr(entity, f.name)
            data[f.name] = None if f.name in RELATIONSHIPS.get(model_class, {}) and value == "" else _serialize_value(value)
        names = list(data)
        cols = ", ".join(f'"{n}"' for n in names)
        placeholders = ", ".join("?" for _ in names)
        updates = ", ".join(f'"{n}"=excluded."{n}"' for n in names[1:])
        self.connection.execute(
            f'INSERT INTO "{model_class.__name__}" ({cols}) VALUES ({placeholders}) '
            f'ON CONFLICT("{names[0]}") DO UPDATE SET {updates}', tuple(data.values()))
        if commit:
            self.connection.commit()

    def get(self, model_class: type[T], object_id: str) -> T | None:
        key = fields(cast(Any, model_class))[0].name
        row = self.connection.execute(
            f'SELECT * FROM "{model_class.__name__}" WHERE "{key}"=?', (object_id,)).fetchone()
        return self._row_to_entity(model_class, row) if row else None

    def list_entities(self, model_class: type[T], where: str = "", params: tuple[Any, ...] = (),
               order: str = "", limit: int | None = None, offset: int = 0) -> list[T]:
        query = f'SELECT * FROM "{model_class.__name__}"'
        if where:
            query += f" WHERE {where}"
        if order:
            query += f" ORDER BY {order}"
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params += (limit, offset)
        return [self._row_to_entity(model_class, row) for row in self.connection.execute(query, params)]

    def _row_to_entity(self, model_class: type[T], row: sqlite3.Row) -> T:
        hints = get_type_hints(model_class)
        data = {}
        for field_info in fields(cast(Any, model_class)):
            if field_info.name == "password_hash" and model_class is d.User:
                account = self.connection.execute(
                    'SELECT password_hash FROM "UserAccount" WHERE user_id=?',
                    (row["user_id"],)).fetchone()
                data[field_info.name] = account[0] if account else ""
                continue
            value = row[field_info.name]
            typ = _field_type(hints[field_info.name])
            if value is None and field_info.name in RELATIONSHIPS.get(model_class, {}):
                value = ""
            if value is not None:
                if typ is datetime:
                    value = datetime.fromisoformat(value)
                elif typ is bool:
                    value = bool(value)
                elif isinstance(typ, type) and issubclass(typ, StrEnum):
                    value = typ(value)
            data[field_info.name] = value
        return model_class(**data)

    def delete(self, model_class: type, object_id: str) -> None:
        if model_class is d.Article:
            self.soft_delete_article(object_id, None)
            return
        key = fields(cast(Any, model_class))[0].name
        self.connection.execute(f'DELETE FROM "{model_class.__name__}" WHERE "{key}"=?', (object_id,))
        self.connection.commit()

    def soft_delete_article(self, article_id: str, user_id: str | None) -> bool:
        """Mark an article deleted and close its pending moderation entries atomically."""
        deleted_at = d.utc_now().isoformat()
        with self.connection:
            changed = self.connection.execute(
                'UPDATE Article SET deleted_at=?, deleted_by=? '
                'WHERE article_id=? AND deleted_at IS NULL',
                (deleted_at, user_id, article_id)).rowcount
            if changed:
                self.connection.execute(
                    'UPDATE ModerationQueueEntry SET processed_at=? '
                    'WHERE article_id=? AND processed_at IS NULL',
                    (deleted_at, article_id))
        return bool(changed)

    def get_article_tags(self, article_id: str) -> list[d.Tag]:
        ids = self.connection.execute('SELECT tag_id FROM article_tag WHERE article_id=?', (article_id,))
        return [tag for row in ids if (tag := self.get(d.Tag, row[0])) is not None]

    def set_article_tags(self, article_id: str, tags: list[d.Tag]) -> None:
        self.connection.execute('DELETE FROM article_tag WHERE article_id=?', (article_id,))
        for tag in tags:
            self.save(tag)
            self.connection.execute('INSERT INTO article_tag VALUES (?, ?, ?)',
                                    (article_id, tag.tag_id, d.utc_now().isoformat()))
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()


class IRepository(ABC, Generic[T]):
    @abstractmethod
    def get_by_id(self, object_id: str) -> T | None: ...

    @abstractmethod
    def save(self, entity: T) -> None: ...

    @abstractmethod
    def delete(self, object_id: str) -> None: ...


class _Repository(IRepository[T]):
    def __init__(self, db: Database, model_class: type[T]) -> None:
        self.db = db
        self.model_class = model_class

    def get_by_id(self, object_id: str) -> T | None:
        return self.db.get(self.model_class, object_id)

    def save(self, entity: T) -> None:
        self.db.save(entity)

    def delete(self, object_id: str) -> None:
        self.db.delete(self.model_class, object_id)


class ArticleRepository(_Repository[d.Article]):
    def __init__(self, db: Database) -> None:
        super().__init__(db, d.Article)

    def get_recent_publications(self) -> list[d.Article]:
        return self.db.list_entities(d.Article, 'publication_status=? AND deleted_at IS NULL',
                              (d.ArticleStatus.PUBLISHED,), 'published_at DESC')

    def save_article(self, article: d.Article) -> None:
        self.save(article)

    def update_status(self, object_id: str, status: str) -> None:
        article = self.get_by_id(object_id)
        if article is None or article.deleted_at is not None:
            raise d.NotFound(object_id)
        article.transition_to(d.ArticleStatus(status))
        self.save(article)


class CommentRepository(_Repository[d.Comment]):
    def __init__(self, db: Database) -> None:
        super().__init__(db, d.Comment)

    def get_by_article(self, article_id: str) -> list[d.Comment]:
        return self.db.list_entities(d.Comment, 'article_id=?', (article_id,), 'added_at')

    def save_comment(self, comment: d.Comment) -> None:
        self.save(comment)

    def update_status(self, object_id: str, status: str) -> None:
        comment = self.get_by_id(object_id)
        if comment is None:
            raise d.NotFound(object_id)
        comment.status = d.CommentStatus(status)
        self.save(comment)


class ComplaintRepository(_Repository[d.Complaint]):
    def __init__(self, db: Database) -> None:
        super().__init__(db, d.Complaint)

    def get_complaint_queue(self) -> list[d.Complaint]:
        return self.db.list_entities(
            d.Complaint,
            'status=? AND comment_id IN (SELECT complaint.comment_id FROM Complaint complaint '
            'JOIN Comment comment ON comment.comment_id=complaint.comment_id '
            'JOIN Article article ON article.article_id=comment.article_id '
            'WHERE article.deleted_at IS NULL AND complaint.status=? '
            'GROUP BY complaint.comment_id HAVING COUNT(DISTINCT complaint.reader_id)>=3)',
            (d.ComplaintStatus.NEW, d.ComplaintStatus.NEW), 'filed_at')

    def save_complaint(self, complaint: d.Complaint) -> None:
        self.save(complaint)

    def get_complaint_count(self, comment_id: str) -> int:
        return self.db.connection.execute(
            'SELECT COUNT(DISTINCT reader_id) FROM Complaint WHERE comment_id=?',
            (comment_id,)).fetchone()[0]

    def get_open_complaint_count(self, comment_id: str) -> int:
        return self.db.connection.execute(
            'SELECT COUNT(DISTINCT reader_id) FROM Complaint WHERE comment_id=? AND status=?',
            (comment_id, d.ComplaintStatus.NEW)).fetchone()[0]


class ReportRepository(_Repository[d.ActivityReport]):
    def __init__(self, db: Database) -> None:
        super().__init__(db, d.ActivityReport)

    def get_reports(self, period: str) -> list[d.ActivityReport]:
        return self.db.list_entities(d.ActivityReport, 'period=?', (period,))

    def save_report(self, report: d.ActivityReport) -> None:
        self.save(report)
