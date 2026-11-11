"""Domain entities from UML E.1 and UI state entities from ER A.7."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DomainException(Exception):
    """A domain invariant has been violated."""


class InvalidTransition(DomainException):
    """The requested state transition is not allowed."""


class PermissionDenied(DomainException):
    """The current user may not perform the operation."""


class NotFound(DomainException):
    """The requested entity does not exist."""


class ArticleStatus(StrEnum):
    DRAFT = "draft"
    IN_MODERATION = "in_moderation"
    NEEDS_REVISION = "needs_revision"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    UNPUBLISHED = "unpublished"


ARTICLE_TRANSITIONS: dict[ArticleStatus, set[ArticleStatus]] = {
    ArticleStatus.DRAFT: {ArticleStatus.IN_MODERATION},
    ArticleStatus.IN_MODERATION: {ArticleStatus.NEEDS_REVISION, ArticleStatus.PUBLISHED},
    ArticleStatus.NEEDS_REVISION: {ArticleStatus.IN_MODERATION},
    ArticleStatus.PUBLISHED: {ArticleStatus.ARCHIVED, ArticleStatus.UNPUBLISHED},
    ArticleStatus.ARCHIVED: {ArticleStatus.PUBLISHED},
    ArticleStatus.UNPUBLISHED: {ArticleStatus.PUBLISHED},
}


class CommentStatus(StrEnum):
    VISIBLE = "visible"
    HIDDEN = "hidden"
    DELETED = "deleted"


class ComplaintStatus(StrEnum):
    NEW = "new"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"


class ReactionType(StrEnum):
    LIKE = "like"
    HELPFUL = "helpful"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class User:
    user_id: str = field(default_factory=new_id)
    full_name: str = ""
    password_hash: str = ""  # Mirrors the account hash in memory; only the account hash is persisted.
    account_id: str = ""


@dataclass
class UserAccount:
    account_id: str = field(default_factory=new_id)
    login: str = ""
    password_hash: str = ""
    is_active: bool = True
    user_id: str = ""
    role_id: str = ""


@dataclass
class Role:
    role_id: str = field(default_factory=new_id)
    role_name: str = ""
    description: str = ""


@dataclass
class AccessPermission:
    permission_id: str = field(default_factory=new_id)
    operation_code: str = ""
    role_id: str = ""


@dataclass
class ContentAuthor:
    author_id: str = field(default_factory=new_id)
    full_name: str = ""
    department: str = ""
    user_id: str = ""


@dataclass
class Editor:
    editor_id: str = field(default_factory=new_id)
    full_name: str = ""
    section: str = ""
    user_id: str = ""


@dataclass
class Reader:
    reader_id: str = field(default_factory=new_id)
    full_name: str = ""
    job_title: str = ""
    user_id: str = ""


@dataclass
class PlatformAdministrator:
    administrator_id: str = field(default_factory=new_id)
    full_name: str = ""
    access_level: str = ""
    user_id: str = ""


@dataclass
class Article:
    article_id: str = field(default_factory=new_id)
    title: str = ""
    content: str = ""
    publication_status: ArticleStatus = ArticleStatus.DRAFT
    author_id: str = ""
    editor_id: str = ""
    category_id: str = ""
    formatting_id: str = ""
    created_at: datetime = field(default_factory=utc_now)
    reviewed_at: datetime | None = None
    classified_at: datetime | None = None
    published_at: datetime | None = None
    view_count: int = 0
    summary: str = ""
    cover_theme: str = ""
    seed_key: str = ""
    deleted_at: datetime | None = None
    deleted_by: str = ""

    def transition_to(self, status: ArticleStatus) -> None:
        if status not in ARTICLE_TRANSITIONS[self.publication_status]:
            raise InvalidTransition(f"{self.publication_status} → {status}")
        self.publication_status = status
        if status == ArticleStatus.PUBLISHED:
            self.published_at = utc_now()

    def ready_for_moderation(self) -> bool:
        return all((self.title.strip(), self.content.strip(), self.category_id))


@dataclass
class Category:
    category_id: str = field(default_factory=new_id)
    name: str = ""
    description: str = ""
    administrator_id: str = ""
    modified_at: datetime = field(default_factory=utc_now)


@dataclass
class Tag:
    tag_id: str = field(default_factory=new_id)
    keyword: str = ""


@dataclass
class MediaAttachment:
    media_id: str = field(default_factory=new_id)
    file_url: str = ""
    content_type: str = ""
    size: int = 0
    article_id: str = ""


@dataclass(frozen=True, slots=True)
class FormattingOptions:
    formatting_id: str = field(default_factory=new_id)
    font: str = "system"
    has_preview: bool = True
    article_id: str = ""


@dataclass
class ModerationQueueEntry:
    queue_entry_id: str = field(default_factory=new_id)
    priority: int = 0
    article_id: str = ""
    editor_id: str = ""
    received_at: datetime = field(default_factory=utc_now)
    processed_at: datetime | None = None


@dataclass
class EditorRemark:
    remark_id: str = field(default_factory=new_id)
    remark_text: str = ""
    severity: Severity = Severity.MEDIUM
    article_id: str = ""
    editor_id: str = ""
    remark_received_at: datetime = field(default_factory=utc_now)
    generated_at: datetime = field(default_factory=utc_now)


@dataclass
class PublicationRecord:
    publication_record_id: str = field(default_factory=new_id)
    result: str = ""
    article_id: str = ""
    editor_id: str = ""
    approved_at: datetime = field(default_factory=utc_now)


@dataclass
class Comment:
    comment_id: str = field(default_factory=new_id)
    text: str = ""
    status: CommentStatus = CommentStatus.VISIBLE
    article_id: str = ""
    reader_id: str = ""
    parent_id: str = ""
    added_at: datetime = field(default_factory=utc_now)
    sent_at: datetime = field(default_factory=utc_now)
    replied_at: datetime | None = None


@dataclass
class Complaint:
    complaint_id: str = field(default_factory=new_id)
    reason: str = ""
    status: ComplaintStatus = ComplaintStatus.NEW
    comment_id: str = ""
    reader_id: str = ""
    filed_at: datetime = field(default_factory=utc_now)


@dataclass
class Reaction:
    reaction_id: str = field(default_factory=new_id)
    reaction_type: ReactionType = ReactionType.LIKE
    article_id: str = ""
    reader_id: str = ""
    marked_at: datetime = field(default_factory=utc_now)


@dataclass
class SearchIndex:
    index_id: str = field(default_factory=new_id)
    lexemes: str = ""
    article_id: str = ""
    index_updated_at: datetime = field(default_factory=utc_now)


@dataclass
class ActivityReport:
    report_id: str = field(default_factory=new_id)
    period: str = ""
    reach_metric: float = 0.0
    administrator_id: str = ""
    generated_at: datetime = field(default_factory=utc_now)
    publication_count: int = 0
    comment_count: int = 0
    reaction_count: int = 0


@dataclass
class InterfaceSubsystem:
    connection_status: str = "disconnected"
    current_theme: str = "light"
    logged_in_at: datetime | None = None
    feed_updated_at: datetime | None = None
    autosaved_at: datetime | None = None
    filter_applied_at: datetime | None = None
    article_opened_at: datetime | None = None
    sessions: list[UserSession] = field(default_factory=list)
    feed: PublicationFeed | None = None
    form: ArticleEditorFormState | None = None
    dashboard: ModeratorDashboardState | None = None
    viewer: ArticleViewerState | None = None


@dataclass
class UserSession:
    session_id: str = field(default_factory=new_id)
    authorization_token: str = field(default_factory=new_id)
    user_id: str = ""
    logged_in_at: datetime = field(default_factory=utc_now)


@dataclass
class PublicationFeed:
    feed_id: str = field(default_factory=new_id)
    current_page: int = 1
    selected_filter: str = ""
    feed_updated_at: datetime | None = None


@dataclass
class ArticleEditorFormState:
    form_id: str = field(default_factory=new_id)
    draft_text: str = ""
    autosave_status: str = "not_saved"
    autosaved_at: datetime | None = None


@dataclass
class ModeratorDashboardState:
    dashboard_id: str = field(default_factory=new_id)
    queue_filter: str = "all"
    filter_applied_at: datetime | None = None


@dataclass
class ArticleViewerState:
    viewer_id: str = field(default_factory=new_id)
    viewed_article_id: str = ""
    article_opened_at: datetime | None = None
