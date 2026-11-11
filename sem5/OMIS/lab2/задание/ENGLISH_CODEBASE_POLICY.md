# OMIS — English-only codebase policy

## Scope and precedence

This document is a binding addendum to `UPGRADE_UI_UX_AUTH_SEED.md` and supersedes the original implementation README **only on naming/language conventions**. The original Russian UML PDF remains authoritative for **entities, attributes, operations, relationships, invariants, and behaviors**. Renaming is not permission to omit them. Do not implement the excluded future-development modules.

## Language contract

- Use English words for **every program identifier**: modules, packages, files, classes, interfaces, functions, methods, parameters, variables, enum names/values, constants, fields, types, ORM classes/columns, SQL table/index/constraint names, API endpoint code identifiers, JSON keys, CSS class names, HTML IDs, test functions, fixture names, shell commands, error codes, and internal logs.
- Use `PascalCase` for classes, `snake_case` for Python identifiers and DB columns, `UPPER_SNAKE_CASE` for constants, and ordinary English semantic names. Never use transliteration (`statya`, `polzovatel`, `rubrika`) and never leave Cyrillic legacy aliases in the runtime.
- Code comments, docstrings, technical messages, internal developer logs, and changelog notes must be in English.
- Russian is permitted for **visible interface text**, the content of published articles/comments, and localized notifications or error messages shown to end users. Keep UI strings in view templates / localization resources rather than embedded in core domain logic. Russian labels in UML mapping documentation are source references, **not code identifiers**.
- Keep all existing UML concepts, attributes, methods, inheritance and associations. Maintain `docs/uml_name_mapping.md`: `Russian UML element / PDF page | English element | kind | implementation path | test path`. Cover both class names and individual fields/operations, not just classes.

## Expected English class names (examples; adapt only when conflicts require it)

| Original UML name | Required English semantic name |
| --- | --- |
| Пользователь | `User` |
| УчетнаяЗапись | `UserAccount` |
| Роль | `Role` |
| ПравоДоступа | `AccessPermission` |
| АвторКонтента | `ContentAuthor` |
| Редактор | `Editor` |
| Читатель | `Reader` |
| АдминистраторПлатформы | `PlatformAdministrator` |
| Статья | `Article` |
| Рубрика | `Category` |
| Тег | `Tag` |
| Медиавложение | `MediaAttachment` |
| ПараметрыОформления | `FormattingOptions` |
| ОчередьМодерации | `ModerationQueueEntry` |
| ЗамечаниеРедактора | `EditorRemark` |
| ПротоколПубликации | `PublicationRecord` |
| Комментарий | `Comment` |
| Жалоба | `Complaint` |
| Реакция | `Reaction` |
| ПоисковыйИндекс | `SearchIndex` |
| ОтчетАктивности | `ActivityReport` |
| IРепозиторий | `IRepository` |
| РепозиторийСтатей | `ArticleRepository` |
| РепозиторийКомментариев | `CommentRepository` |
| РепозиторийЖалоб | `ComplaintRepository` |
| РепозиторийОтчетов | `ReportRepository` |
| КонтроллерПубликаций | `PublicationController` |
| КонтроллерМодерации | `ModerationController` |
| КонтроллерУведомлений | `NotificationController` |
| КонтроллерЛенты | `FeedController` |
| КонтроллерОтчетов | `ReportController` |
| IСтратегияМодерации | `IModerationStrategy` |
| СтратегияРучнойМодерации | `ManualModerationStrategy` |
| СтратегияАвтоФильтрации | `AutoFilterStrategy` |
| IКоманда | `ICommand` |
| КомандаПубликации | `PublishArticleCommand` |
| КомандаОтклоненияСтатьи | `RejectArticleCommand` |
| КомандаСкрытияКомментария | `HideCommentCommand` |
| КомандаУдаленияКомментария | `DeleteCommentCommand` |
| IПредставление | `IView` |
| БазовоеПредставление | `BaseView` |
| IПредставлениеЛенты | `IFeedView` |
| IПредставлениеФормыРедактора | `IArticleEditorView` |
| IПредставлениеКабинетаМодератора | `IModeratorDashboardView` |
| IПредставлениеЧтенияСтатьи | `IArticleDetailView` |
| КонтейнерЗависимостей | `DependencyContainer` |
| ФабрикаКонтроллеров | `ControllerFactory` |
| ФабрикаПредставлений | `ViewFactory` |
| КонфигураторСистемы | `SystemConfigurator` |
| ПриложениеБлогПлатформы | `BlogPlatformApp` |
| ИнтерфейснаяПодсистема | `InterfaceSubsystem` |
| СессияПользователя | `UserSession` |
| ЛентаПубликаций | `PublicationFeed` |
| ФормаРедактора | `ArticleEditorFormState` |
| КабинетМодератора | `ModeratorDashboardState` |
| ОкноЧтенияСтатьи | `ArticleViewerState` |

The table is a **starting mapping**, not a replacement for the exhaustive `docs/uml_name_mapping.md`. Add every field, operation and association from the PDF. Examples of field mappings: `идСтатьи -> article_id`, `заголовок -> title`, `содержание -> content`, `статусПубликации -> publication_status`, `текущаяСтраница -> current_page`, `выбранныйФильтр -> selected_filter`, `статусАвтосохранения -> autosave_status`. Examples of method mappings: `получитьПоИд -> get_by_id`, `сохранить -> save`, `удалить -> delete`, `валидироватьПоля -> validate_fields`, `опубликоватьМатериал -> publish_material`, `проверитьПорогСкрытия -> has_reached_hide_threshold`.

## Safe refactoring strategy

1. Inventory existing Python identifiers, ORM models, SQL schema identifiers, route handlers, template variables, CSS/JS names, test fixtures, DI bindings, import paths, CLI commands and any external serialized formats. Identify what is **actually** Cyrillic before changing anything.
2. Write the mapping and snapshot current test outcomes; back up existing SQLite database and test migrations with a copy.
3. Rename code symbols consistently across domains, repositories, controllers, interfaces, DI container/factories, views, routes, templates, scripts and tests. Do **not** create redundant parallel classes or maintain Cyrillic runtime aliases.
4. If schema names need changing, use a real migration preserving all existing records, keys, foreign keys, indexes and relationships. Legacy names may be referenced as **data in migration-only compatibility definitions** when strictly needed; they must not remain as declared identifiers or new-schema names. Never drop or regenerate a user's DB for convenience.
5. Preserve contracts and security. Retain hashed passwords, role checks, state transitions, editor approvals, notifications, media, search, report aggregation, session validity and CSRF protection. Update seed code and test fixtures to the new names.
6. Verify `pytest`, `ruff`, `mypy`, DB round-trip/reopen, browser flows and `python3 scripts/check_english_identifiers.py .`. Check JS/CSS/HTML/SQL naming separately. Test at least one existing user record through any migration and one newly registered author through the full publication workflow.

## Done when

- There are **zero Cyrillic Python identifiers** (including attributes, imports and arguments), no transliterated domain names, and no Cyrillic identifiers in the current DB schema, templates/CSS/JS, JSON keys or public API.
- Russian appears only in end-user UI text and user-created/demo content, plus immutable source PDF and mapping documentation for original UML terms.
- `docs/uml_name_mapping.md` covers all mandatory classes, attributes, methods and links. All required behavior still works and all tests pass.
- Document migration steps and test evidence; report changes and any remaining constraints instead of claiming unverified completion.
