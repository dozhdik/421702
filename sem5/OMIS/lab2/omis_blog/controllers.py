"""The five baseline E.2 controllers and their user workflows."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, time, timezone
from typing import Any

from omis_blog import domain as d
from omis_blog.localization import message
from omis_blog.patterns import (
    IModerationStrategy, RejectArticleCommand, PublishArticleCommand,
    HideCommentCommand, DeleteCommentCommand,
    ManualModerationStrategy,
)
from omis_blog.storage import (
    Database, ComplaintRepository, CommentRepository,
    ReportRepository, ArticleRepository,
)


class NotificationController:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.current_complainant = ""

    def send(self, recipient: str, text: str) -> None:
        self.db.connection.execute('INSERT INTO notification VALUES (?, ?, ?, ?, 0)',
                                   (d.new_id(), recipient, text, d.utc_now().isoformat()))
        self.db.connection.commit()

    def notify_editor(self, article_id: str) -> None:
        editors = self.db.list_entities(d.Editor)
        for editor in editors:
            self.send(editor.user_id, message("article_awaits_review", article_id=article_id))

    def send_warning(self, reader_id: str) -> None:
        reader = self.db.get(d.Reader, reader_id)
        if reader:
            self.send(reader.user_id, message("comment_removed_warning"))

    def notify_complainant(self, result: str, reader_id: str = "") -> None:
        target = reader_id or self.current_complainant
        if not target:
            raise d.DomainException("missing_complainant")
        reader = self.db.get(d.Reader, target)
        if reader is None:
            raise d.NotFound(target)
        self.send(reader.user_id, result)

    def inbox(self, user_id: str) -> list[sqlite3.Row]:
        return list(self.db.connection.execute(
            'SELECT * FROM notification WHERE recipient=? ORDER BY created_at DESC', (user_id,)))


class PublicationController:
    def __init__(self, repository: ArticleRepository,
                 notifications: NotificationController | None = None) -> None:
        self.article_repository = repository
        self.db = repository.db
        self.notifications = notifications or NotificationController(self.db)
        self.view: Any = None
        self.commands: list[Any] = []

    def validate_fields(self, article: d.Article) -> bool:
        return article.ready_for_moderation()

    def process_submission(self, article: d.Article) -> None:
        if article.deleted_at is not None:
            raise d.NotFound(article.article_id)
        if not self.validate_fields(article):
            raise d.DomainException("article_missing_required_fields")
        article.transition_to(d.ArticleStatus.IN_MODERATION)
        self.article_repository.save_article(article)
        self.db.save(d.ModerationQueueEntry(article_id=article.article_id))
        self.notifications.notify_editor(article.article_id)
        if self.view:
            self.view.refresh(d.ArticleStatus.IN_MODERATION)

    def publish_material(self, article_id: str, editor_id: str = "") -> None:
        article = self.article_repository.get_by_id(article_id)
        if article is None or article.deleted_at is not None:
            raise d.NotFound(article_id)
        command = PublishArticleCommand(self.article_repository, article_id)
        command.execute()
        self.commands.append(command)
        article = self.article_repository.get_by_id(article_id)
        assert article is not None
        article.editor_id = editor_id
        article.reviewed_at = d.utc_now()
        self.article_repository.save(article)
        self.db.save(d.PublicationRecord(
            result="approved", article_id=article_id, editor_id=editor_id))
        self.update_index(d.SearchIndex(article_id=article_id))
        self._close_queue_entries(article_id, editor_id)
        author = self.db.get(d.ContentAuthor, article.author_id)
        if author:
            self.notifications.send(author.user_id, message("article_published"))

    def return_for_revision(self, article_id: str, editor_id: str, text: str) -> None:
        article = self.article_repository.get_by_id(article_id)
        if article is None or article.deleted_at is not None:
            raise d.NotFound(article_id)
        if not text.strip():
            raise d.DomainException("remark_required")
        command = RejectArticleCommand(self.article_repository, article_id)
        command.execute()
        self.commands.append(command)
        article = self.article_repository.get_by_id(article_id)
        assert article is not None
        article.editor_id = editor_id
        article.reviewed_at = d.utc_now()
        self.article_repository.save(article)
        self.db.save(d.EditorRemark(
            remark_text=text, article_id=article_id, editor_id=editor_id))
        self._close_queue_entries(article_id, editor_id)
        author = self.db.get(d.ContentAuthor, article.author_id)
        if author:
            self.notifications.send(author.user_id, message("article_needs_revision", remark=text))

    def _close_queue_entries(self, article_id: str, editor_id: str) -> None:
        for ticket in self.db.list_entities(d.ModerationQueueEntry,
                                     'article_id=? AND processed_at IS NULL', (article_id,)):
            ticket.editor_id = editor_id
            ticket.processed_at = d.utc_now()
            self.db.save(ticket)

    def update_index(self, index: d.SearchIndex) -> None:
        article = self.article_repository.get_by_id(index.article_id)
        if article is None or article.deleted_at is not None:
            raise d.NotFound(index.article_id)
        existing = self.db.list_entities(d.SearchIndex, 'article_id=?', (article.article_id,))
        if existing:
            index.index_id = existing[0].index_id
        tags = " ".join(tag.keyword for tag in self.db.get_article_tags(article.article_id))
        author = self.db.get(d.ContentAuthor, article.author_id)
        rubric = self.db.get(d.Category, article.category_id)
        index.lexemes = " ".join((article.title, article.content, tags,
                                    author.full_name if author else "", rubric.name if rubric else "")).casefold()
        index.index_updated_at = d.utc_now()
        self.db.save(index)


class ModerationController:
    def __init__(self, comment_repository: CommentRepository, complaint_repository: ComplaintRepository,
                 strategy: IModerationStrategy | None = None,
                 notifications: NotificationController | None = None) -> None:
        self.comment_repository = comment_repository
        self.complaint_repository = complaint_repository
        self.db = comment_repository.db
        self.strategy = strategy or ManualModerationStrategy()
        self.notifications = notifications or NotificationController(self.db)
        self.current_complaint: str = ""
        self.commands: list[Any] = []
        self.view: Any = None

    def register_complaint(self, complaint: d.Complaint) -> None:
        comment = self.comment_repository.get_by_id(complaint.comment_id)
        if comment is None:
            raise d.NotFound(complaint.comment_id)
        article = self.db.get(d.Article, comment.article_id)
        if article is None or article.deleted_at is not None:
            raise d.NotFound(comment.article_id)
        if comment.status == d.CommentStatus.DELETED:
            raise d.DomainException("comment_deleted")
        try:
            self.complaint_repository.save_complaint(complaint)
        except sqlite3.IntegrityError as exc:
            raise d.DomainException("duplicate_complaint") from exc
        self.current_complaint = complaint.complaint_id
        if self.has_reached_hide_threshold(complaint.comment_id) and comment.status == d.CommentStatus.VISIBLE:
            command = HideCommentCommand(self.comment_repository, complaint.comment_id)
            command.execute()
            self.commands.append(command)
            for editor in self.db.list_entities(d.Editor):
                self.notifications.send(editor.user_id, message("complaint_needs_review"))
            if self.view:
                self.view.refresh(self.complaint_repository.get_complaint_queue())

    def has_reached_hide_threshold(self, comment_id: str) -> bool:
        return self.complaint_repository.get_open_complaint_count(comment_id) >= 3

    def apply_decision(self, verdict: str, comment_id: str = "") -> None:
        if not comment_id and self.current_complaint:
            complaint = self.complaint_repository.get_by_id(self.current_complaint)
            comment_id = complaint.comment_id if complaint else ""
        comment = self.comment_repository.get_by_id(comment_id)
        if comment is None:
            raise d.NotFound(comment_id)
        article = self.db.get(d.Article, comment.article_id)
        if article is None or article.deleted_at is not None:
            raise d.NotFound(comment.article_id)
        complaints = self.db.list_entities(d.Complaint, 'comment_id=? AND status=?',
                                    (comment_id, d.ComplaintStatus.NEW))
        if not complaints:
            raise d.DomainException("no_open_complaints")
        if verdict == "confirm":
            command = DeleteCommentCommand(self.comment_repository, comment_id)
            command.execute()
            self.commands.append(command)
            self.notifications.send_warning(comment.reader_id)
            status = d.ComplaintStatus.CONFIRMED
            result = message("complaint_confirmed")
        elif verdict == "dismiss":
            if not self.strategy.check(comment.text):
                raise d.DomainException("restore_blocked_by_strategy")
            self.comment_repository.update_status(comment_id, d.CommentStatus.VISIBLE)
            status = d.ComplaintStatus.DISMISSED
            result = message("complaint_dismissed")
        else:
            raise d.DomainException("unknown_verdict")
        for complaint in complaints:
            complaint.status = status
            self.complaint_repository.save(complaint)
            self.notifications.notify_complainant(result, complaint.reader_id)


class FeedController:
    def __init__(self, repository: ArticleRepository) -> None:
        self.article_repository = repository
        self.db = repository.db
        self.view: Any = None

    def get_feed_updates(self) -> list[d.Article]:
        articles = self.article_repository.get_recent_publications()
        if self.view:
            self.view.refresh(articles)
        return articles

    def filter_by_category(self, category_id: str) -> list[d.Article]:
        return [x for x in self.get_feed_updates() if x.category_id == category_id]

    def search(self, query: str = "", author: str = "", category: str = "",
              tag: str = "", page: int = 1, size: int = 10) -> list[d.Article]:
        result = self.get_feed_updates()
        if query:
            indexed = {x.article_id for x in self.db.list_entities(d.SearchIndex)
                       if query.casefold() in x.lexemes}
            result = [x for x in result if x.article_id in indexed]
        if author:
            result = [x for x in result if (a := self.db.get(d.ContentAuthor, x.author_id))
                      and author.casefold() in a.full_name.casefold()]
        if category:
            result = [x for x in result if x.category_id == category]
        if tag:
            result = [x for x in result if any(t.keyword.casefold() == tag.casefold()
                                               for t in self.db.get_article_tags(x.article_id))]
        start = max(0, page - 1) * size
        return result[start:start + size]


class ReportController:
    def __init__(self, repository: ReportRepository) -> None:
        self.report_repository = repository
        self.db = repository.db
        self.view: Any = None

    def generate_report(self, period: str) -> d.ActivityReport:
        try:
            start_s, end_s = period.split("/", 1)
            start = datetime.combine(date.fromisoformat(start_s), time.min, timezone.utc).isoformat()
            end = datetime.combine(date.fromisoformat(end_s), time.max, timezone.utc).isoformat()
        except ValueError as exc:
            raise d.DomainException("invalid_period_format") from exc
        if start > end:
            raise d.DomainException("period_start_after_end")
        db = self.db.connection
        def count(table: str, col: str) -> int:
            return int(db.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE "{col}" BETWEEN ? AND ?',
                (start, end)).fetchone()[0])
        published = self.db.list_entities(d.Article, 'published_at BETWEEN ? AND ?', (start, end))
        views = db.execute('SELECT COUNT(*) FROM article_view WHERE created_at BETWEEN ? AND ?',
                           (start, end)).fetchone()[0]
        result = d.ActivityReport(period=period, reach_metric=float(views),
                                   publication_count=len(published),
                                   comment_count=count("Comment", "added_at"),
                                   reaction_count=count("Reaction", "marked_at"))
        self.report_repository.save_report(result)
        if self.view:
            self.view.display(result)
        return result

    def get_reports(self) -> list[d.ActivityReport]:
        return self.db.list_entities(d.ActivityReport, order='generated_at DESC')
