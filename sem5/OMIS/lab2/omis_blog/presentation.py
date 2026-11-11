"""E.3 view contracts and concrete HTML view state."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from omis_blog import domain as d


class IView(ABC):
    @abstractmethod
    def display(self, data: Any) -> None: ...

    @abstractmethod
    def refresh(self, data: Any) -> None: ...


class BaseView(IView, ABC):
    def __init__(self) -> None:
        self.view_id = d.new_id()
        self.data: Any = None

    @abstractmethod
    def display(self, data: Any) -> None:
        self.data = data

    def refresh(self, data: Any) -> None:
        self.data = data


class IFeedView(IView, ABC):
    @abstractmethod
    def display_feed(self, articles: list[d.Article]) -> None: ...

    @abstractmethod
    def apply_filter(self, selected_filter: str) -> None: ...


class IArticleEditorView(IView, ABC):
    @abstractmethod
    def display_draft(self, draft_text: str) -> None: ...

    @abstractmethod
    def show_autosave_status(self, status: str) -> None: ...


class IModeratorDashboardView(IView, ABC):
    @abstractmethod
    def display_queue(self, queue_filter: str) -> None: ...

    @abstractmethod
    def show_tickets(self, complaints: list[d.Complaint]) -> None: ...


class IArticleDetailView(IView, ABC):
    @abstractmethod
    def open_article(self, article_id: str) -> None: ...

    @abstractmethod
    def display_comments(self, comment_count: list[d.Comment]) -> None: ...


class FeedView(BaseView, IFeedView):
    def __init__(self, controller: Any) -> None:
        super().__init__()
        self.controller = controller
        self.state = d.PublicationFeed()

    def display(self, data: Any) -> None:
        super().display(data)

    def display_feed(self, articles: list[d.Article]) -> None:
        self.display(articles)
        self.state.feed_updated_at = d.utc_now()

    def apply_filter(self, selected_filter: str) -> None:
        self.state.selected_filter = selected_filter
        self.state.feed_updated_at = d.utc_now()
        self.refresh(self.controller.filter_by_category(selected_filter))


class ArticleEditorView(BaseView, IArticleEditorView):
    def __init__(self, controller: Any) -> None:
        super().__init__()
        self.controller = controller
        self.state = d.ArticleEditorFormState()

    def display(self, data: Any) -> None:
        super().display(data)

    def display_draft(self, draft_text: str) -> None:
        self.state.draft_text = draft_text
        self.display(draft_text)

    def show_autosave_status(self, status: str) -> None:
        self.state.autosave_status = status
        self.state.autosaved_at = d.utc_now()
        self.refresh(status)


class ModeratorDashboardView(BaseView, IModeratorDashboardView):
    def __init__(self, controller: Any) -> None:
        super().__init__()
        self.controller = controller
        self.state = d.ModeratorDashboardState()

    def display(self, data: Any) -> None:
        super().display(data)

    def display_queue(self, queue_filter: str) -> None:
        self.state.queue_filter = queue_filter
        self.state.filter_applied_at = d.utc_now()
        self.display(queue_filter)

    def show_tickets(self, complaints: list[d.Complaint]) -> None:
        self.refresh(complaints)


class ArticleDetailView(BaseView, IArticleDetailView):
    def __init__(self, controller: Any) -> None:
        super().__init__()
        self.controller = controller
        self.state = d.ArticleViewerState()

    def display(self, data: Any) -> None:
        super().display(data)

    def open_article(self, article_id: str) -> None:
        self.state.viewed_article_id = article_id
        self.state.article_opened_at = d.utc_now()
        self.display(article_id)

    def display_comments(self, comment_count: list[d.Comment]) -> None:
        self.refresh(comment_count)


class ReportView(BaseView):
    """Shared view contract for reports without a separate UML interface."""

    def display(self, data: Any) -> None:
        super().display(data)
