"""Машинная инвентаризация публичных элементов базовых диаграмм A и E."""

from dataclasses import fields
from inspect import isabstract

from omis_blog import controllers, domain, infrastructure, main, patterns, presentation, storage


DOMAIN_FIELDS = {
    "User": "user_id full_name password_hash",
    "UserAccount": "account_id login password_hash is_active",
    "Role": "role_id role_name description",
    "AccessPermission": "permission_id operation_code",
    "ContentAuthor": "author_id full_name department",
    "Editor": "editor_id full_name section",
    "Reader": "reader_id full_name job_title",
    "PlatformAdministrator": "administrator_id full_name access_level",
    "Article": "article_id title content publication_status",
    "Category": "category_id name description",
    "Tag": "tag_id keyword",
    "MediaAttachment": "media_id file_url content_type size",
    "FormattingOptions": "formatting_id font has_preview",
    "ModerationQueueEntry": "queue_entry_id priority",
    "EditorRemark": "remark_id remark_text severity",
    "PublicationRecord": "publication_record_id result",
    "Comment": "comment_id text status",
    "Complaint": "complaint_id reason status",
    "Reaction": "reaction_id reaction_type",
    "SearchIndex": "index_id lexemes",
    "ActivityReport": "report_id period reach_metric",
    "InterfaceSubsystem": "connection_status current_theme",
    "UserSession": "session_id authorization_token",
    "PublicationFeed": "feed_id current_page selected_filter",
    "ArticleEditorFormState": "form_id draft_text autosave_status",
    "ModeratorDashboardState": "dashboard_id queue_filter",
    "ArticleViewerState": "viewer_id viewed_article_id",
}

METHODS = {
    storage: {
        "IRepository": "get_by_id save delete",
        "ArticleRepository": "get_recent_publications save_article update_status get_by_id save delete",
        "CommentRepository": "get_by_article save_comment update_status get_by_id save delete",
        "ComplaintRepository": "get_complaint_queue save_complaint get_complaint_count get_by_id save delete",
        "ReportRepository": "get_reports save_report get_by_id save delete",
    },
    controllers: {
        "PublicationController": "process_submission validate_fields publish_material update_index",
        "ModerationController": "register_complaint apply_decision has_reached_hide_threshold",
        "NotificationController": "notify_editor send_warning notify_complainant",
        "FeedController": "get_feed_updates filter_by_category",
        "ReportController": "generate_report get_reports",
    },
    patterns: {
        "IModerationStrategy": "check",
        "ManualModerationStrategy": "check",
        "AutoFilterStrategy": "check",
        "ICommand": "execute undo",
        "PublishArticleCommand": "execute undo",
        "RejectArticleCommand": "execute undo",
        "HideCommentCommand": "execute undo",
        "DeleteCommentCommand": "execute undo",
    },
    presentation: {
        "IView": "display refresh",
        "BaseView": "display refresh",
        "IFeedView": "display_feed apply_filter",
        "IArticleEditorView": "display_draft show_autosave_status",
        "IModeratorDashboardView": "display_queue show_tickets",
        "IArticleDetailView": "open_article display_comments",
        "FeedView": "display refresh display_feed apply_filter",
        "ArticleEditorView": "display refresh display_draft show_autosave_status",
        "ModeratorDashboardView": "display refresh display_queue show_tickets",
        "ArticleDetailView": "display refresh open_article display_comments",
    },
    infrastructure: {
        "DependencyContainer": "register resolve create_controller create_view",
        "ControllerFactory": "create_publication_controller create_moderation_controller create_notification_controller create_feed_controller create_report_controller",
        "ViewFactory": "create_feed_view create_editor_view create_dashboard_view create_article_detail_view",
        "SystemConfigurator": "configure_dependencies create_repositories create_controllers create_views connect_components",
    },
    main: {"BlogPlatformApp": "main initialize_system start_application stop_application"},
}


def test_all_base_entity_fields_and_classes_exist():
    for name, required in DOMAIN_FIELDS.items():
        cls = getattr(domain, name)
        assert set(required.split()) <= {item.name for item in fields(cls)}
    assert len(storage.ENTITIES) == 22  # 21 E.1 + сессия A.7


def test_all_base_operations_are_callable():
    for module, classes in METHODS.items():
        for name, names in classes.items():
            cls = getattr(module, name)
            assert all(callable(getattr(cls, method, None)) for method in names.split())
            if not name.startswith("I") and name != "BaseView":
                assert not isabstract(cls)
    assert isabstract(presentation.BaseView)
