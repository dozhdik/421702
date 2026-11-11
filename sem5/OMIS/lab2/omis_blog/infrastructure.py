"""Container, factories, and configurator from baseline diagrams E.4–E.5."""

from __future__ import annotations

import inspect
from typing import Any

from omis_blog.controllers import (
    FeedController, ModerationController, ReportController,
    PublicationController, NotificationController,
)
from omis_blog.patterns import IModerationStrategy, ManualModerationStrategy
from omis_blog.presentation import (
    IModeratorDashboardView, IFeedView,
    IArticleEditorView, IArticleDetailView,
    ModeratorDashboardView, FeedView,
    ArticleEditorView, ReportView, ArticleDetailView,
)
from omis_blog.storage import (
    IRepository, Database, ComplaintRepository, CommentRepository,
    ReportRepository, ArticleRepository,
)


class DependencyContainer:
    def __init__(self) -> None:
        self.registry: dict[type, type | Any] = {}
        self.controller_factory: ControllerFactory | None = None
        self.view_factory: ViewFactory | None = None

    def register(self, interface_type: type, implementation: type | Any) -> None:
        self.registry[interface_type] = implementation

    def resolve(self, interface_type: type) -> Any:
        if interface_type not in self.registry:
            raise KeyError(interface_type)
        value = self.registry[interface_type]
        if not inspect.isclass(value):
            return value
        if value is interface_type and not inspect.isabstract(value):
            return value()
        if value is not interface_type and not inspect.isabstract(value):
            return value()
        raise TypeError(f"Cannot create {interface_type.__name__}")

    def create_controller(self, component_type: type) -> Any:
        return self.resolve(component_type)

    def create_view(self, component_type: type) -> Any:
        return self.resolve(component_type)


class ControllerFactory:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.notifications = NotificationController(db)

    def create_publication_controller(self, repository: ArticleRepository) -> PublicationController:
        return PublicationController(repository, self.notifications)

    def create_moderation_controller(self, comment_repository: CommentRepository,
                                  complaint_repository: ComplaintRepository) -> ModerationController:
        return ModerationController(comment_repository, complaint_repository, ManualModerationStrategy(), self.notifications)

    def create_notification_controller(self) -> NotificationController:
        return self.notifications

    def create_feed_controller(self, repository: ArticleRepository) -> FeedController:
        return FeedController(repository)

    def create_report_controller(self, repository: ReportRepository) -> ReportController:
        return ReportController(repository)


class ViewFactory:
    def create_feed_view(self, controller: FeedController) -> IFeedView:
        return FeedView(controller)

    def create_editor_view(self, controller: PublicationController) -> IArticleEditorView:
        return ArticleEditorView(controller)

    def create_dashboard_view(self, controller: ModerationController) -> IModeratorDashboardView:
        return ModeratorDashboardView(controller)

    def create_article_detail_view(self, controller: ModerationController) -> IArticleDetailView:
        return ArticleDetailView(controller)


class SystemConfigurator:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.container: DependencyContainer | None = None
        self.repositories: list[Any] = []
        self.controllers: list[Any] = []
        self.views: list[Any] = []

    def configure_dependencies(self, container: DependencyContainer) -> None:
        self.container = container
        container.controller_factory = ControllerFactory(self.db)
        container.view_factory = ViewFactory()
        container.register(Database, self.db)
        container.register(IModerationStrategy, ManualModerationStrategy)

    def create_repositories(self) -> list[Any]:
        self.repositories = [ArticleRepository(self.db), CommentRepository(self.db),
                            ComplaintRepository(self.db), ReportRepository(self.db)]
        if self.container:
            for repo in self.repositories:
                self.container.register(type(repo), repo)
            self.container.register(IRepository, self.repositories[0])
        return self.repositories

    def create_controllers(self, repositories: list[Any]) -> list[Any]:
        assert self.container and self.container.controller_factory
        articles, comments, complaints, reports = repositories
        factory = self.container.controller_factory
        self.controllers = [factory.create_publication_controller(articles),
                            factory.create_moderation_controller(comments, complaints),
                            factory.create_notification_controller(),
                            factory.create_feed_controller(articles),
                            factory.create_report_controller(reports)]
        for controller in self.controllers:
            self.container.register(type(controller), controller)
        return self.controllers

    def create_views(self, controllers: list[Any]) -> list[Any]:
        assert self.container and self.container.view_factory
        pub, mod, _, feed, _ = controllers
        factory = self.container.view_factory
        self.views = [factory.create_feed_view(feed),
                              factory.create_editor_view(pub),
                              factory.create_dashboard_view(mod),
                              factory.create_article_detail_view(mod)]
        for interface, view in zip((IFeedView, IArticleEditorView,
                                    IModeratorDashboardView, IArticleDetailView),
                                   self.views):
            self.container.register(interface, view)
        return self.views

    def connect_components(self) -> None:
        pub, mod, _, feed, reports = self.controllers
        feed.view = self.views[0]
        pub.view = self.views[1]
        mod.view = self.views[2]
        reports.view = ReportView()

