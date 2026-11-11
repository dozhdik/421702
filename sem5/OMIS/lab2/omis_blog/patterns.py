"""Strategy and Command patterns with reversible state changes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from omis_blog import domain as d
from omis_blog.storage import CommentRepository, ArticleRepository


class IModerationStrategy(ABC):
    @abstractmethod
    def check(self, content: str) -> bool: ...


class ManualModerationStrategy(IModerationStrategy):
    def check(self, content: str) -> bool:
        return bool(content.strip())


class AutoFilterStrategy(IModerationStrategy):
    def __init__(self, stop_words: set[str] | None = None) -> None:
        self.stop_words = {word.casefold() for word in (stop_words or set())}

    def check(self, content: str) -> bool:
        words = set(content.casefold().split())
        return bool(content.strip()) and not bool(words & self.stop_words)


class ICommand(ABC):
    @abstractmethod
    def execute(self) -> None: ...

    @abstractmethod
    def undo(self) -> None: ...


class _ArticleCommand(ICommand):
    new_status: d.ArticleStatus

    def __init__(self, repository: ArticleRepository, article_id: str) -> None:
        self.repository = repository
        self.article_id = article_id
        self.previous_status: d.ArticleStatus | None = None
        self.previous_date: datetime | None = None

    def execute(self) -> None:
        article = self.repository.get_by_id(self.article_id)
        if article is None:
            raise d.NotFound(self.article_id)
        self.previous_status = article.publication_status
        self.previous_date = article.published_at
        article.transition_to(self.new_status)
        self.repository.save(article)

    def undo(self) -> None:
        if self.previous_status is None:
            raise d.DomainException("command_not_executed")
        article = self.repository.get_by_id(self.article_id)
        if article is None:
            raise d.NotFound(self.article_id)
        article.publication_status = self.previous_status
        article.published_at = self.previous_date
        self.repository.save(article)


class PublishArticleCommand(_ArticleCommand):
    new_status = d.ArticleStatus.PUBLISHED


class RejectArticleCommand(_ArticleCommand):
    new_status = d.ArticleStatus.NEEDS_REVISION


class _CommentCommand(ICommand):
    new_status: d.CommentStatus

    def __init__(self, repository: CommentRepository, comment_id: str) -> None:
        self.repository = repository
        self.comment_id = comment_id
        self.previous_status: d.CommentStatus | None = None

    def execute(self) -> None:
        comment = self.repository.get_by_id(self.comment_id)
        if comment is None:
            raise d.NotFound(self.comment_id)
        self.previous_status = comment.status
        comment.status = self.new_status
        self.repository.save(comment)

    def undo(self) -> None:
        if self.previous_status is None:
            raise d.DomainException("command_not_executed")
        self.repository.update_status(self.comment_id, self.previous_status)


class HideCommentCommand(_CommentCommand):
    new_status = d.CommentStatus.HIDDEN


class DeleteCommentCommand(_CommentCommand):
    new_status = d.CommentStatus.DELETED
