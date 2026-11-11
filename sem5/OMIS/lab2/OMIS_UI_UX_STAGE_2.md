# OMIS — UI/UX Stage 2: Editorial Redesign

> Implementation specification for Codex. This document is an incremental improvement request for the existing working corporate blogging platform, **not** a request to rebuild it.
>
> Scope: presentation, navigation, accessibility, responsive layout, interaction feedback, and usability. Preserve existing domain logic, storage, authentication, moderation, reports, article deletion, and the base UML contracts.

## 0. Baseline and non-negotiable constraints

The latest implementation has been manually checked by the product owner: five demonstration articles appear; new-user registration works; a new author can create a draft, sign out and back in without losing it, submit it for moderation; an editor can see and approve it; the published article appears in the feed; article soft deletion has been checked.

The app currently uses Python 3.11+, `wsgiref`, `sqlite3`, server-rendered HTML, `omis_blog/web.py`, `omis_blog/site.css`, presentation adapters in `omis_blog/presentation.py`, and components wired by `omis_blog/infrastructure.py`. Verify actual current structure before editing: prior documentation may lag the code.

**Rules**

1. **All code identifiers and technical code comments must be English.** This includes Python classes, methods, variables, HTML `id`/`name` values, CSS class selectors, JavaScript identifiers, SQL entities and values, route names, test names, and filenames. **Russian is allowed and expected only in visible UI copy and article/user-authored content.** Existing UML documentation may reproduce Russian labels solely as a historical source-to-code mapping; do not add Cyrillic identifiers or runtime aliases.
2. Preserve all base UML A/E classes, fields, methods and relationships, including existing English mappings in `docs/uml_name_mapping.md`. Do not implement the explicitly excluded future directions (version history, scheduled publication, multilingual or multitenant modules).
3. Do not swap out WSGI/SQLite for another framework, introduce React/Vue, or add a Node build step. Do not use external CDNs, remote fonts, paid services or API keys. The application must still run fully offline/locally.
4. No database schema migrations are required or authorized for this redesign. If a presentation decision really needs a new stored attribute, prefer deriving it from existing data. Explain any unavoidable exception before implementing it.
5. Preserve URL behavior and all existing features: login, registration, logout, draft saving/autosaving, `My Articles`, upload/delete media, tag/category filters, search, moderation, editor remarks, publication, reactions, comments, complaints, notifications, admin operations and reports, and **article soft delete with confirmation**.
6. Keep the current public feed readable without login. Do not show private/draft/moderation content to unauthorized visitors. Permission checks and CSRF remain server-side.
7. No fake buttons, non-functional controls, hard-coded counters or seeded UI copy masquerading as live data. Every visible action must be wired to an existing functional workflow or not displayed.
8. Implement in small steps and run the full pre-existing regression suite after each step. Do not replace real tests with snapshots alone.

## 1. Design direction

Create a clean, restrained **editorial platform for corporate writing**: modern, readable, calm, with clear hierarchy and one consistent visual language. Avoid a crowded admin-panel look on public reading pages. This is a polished product UI, not a pixel-perfect recreation of PDF mockups.

Use a light theme (the existing app has no functional theme toggle), system font stack, high contrast and generous whitespace. Do not introduce a decorative dark-mode button. Use CSS-created category covers where actual images do not exist; uploaded real images should remain visible where available.

### 1.1 Suggested design tokens (may be adjusted for WCAG contrast)

Add reusable CSS custom properties in `omis_blog/site.css`, not scattered literal colors:

```css
:root {
  --color-page: #f7f8fb;
  --color-surface: #ffffff;
  --color-surface-muted: #f0f3f8;
  --color-ink: #172239;
  --color-ink-muted: #526176;
  --color-border: #e0e5ee;
  --color-primary: #315bea;
  --color-primary-hover: #2549ca;
  --color-success: #167453;
  --color-warning: #8a5809;
  --color-danger: #ad2d39;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 18px;
  --shadow-card: 0 6px 24px rgb(23 34 57 / 6%);
  --layout-width: 1160px;
  --reading-width: 760px;
}
```

Token colors are starting values, not an exception from contrast testing. Design target: minimal decorative elements; soft shadows; meaningful blue primary actions; subdued secondary actions; red **only** for destructive actions.

### 1.2 Typography and spacing

- System UI font for navigation/actions and a highly readable system serif or sans for long articles; no remote font downloads.
- 16px body text minimum on small screens, approximate 1.5 line-height for interfaces and 1.65–1.8 for article paragraphs.
- Strong hierarchy: site title / article title / section heading / body / metadata. Do not use small gray text for essential information.
- Use a consistent spacing scale (4, 8, 12, 16, 24, 32, 48 px), maximum container widths, sensible card padding and comfortable whitespace.
- Page layout must be usable without horizontal scrolling at 360px.

## 2. Reusable components and layout

Consolidate presentation markup and styling into consistent reusable render helpers/components **within the existing architecture** (server-side HTML helpers or presentation adapters). Refactor `web.py` only enough to reduce duplication; do not refactor core services while redesigning.

**Common components:**

- Header with a textual logo/brand, navigation to feed, `My Articles` (when authorized), moderation (for editor), admin area (for admin), notifications, and login/account/logout; on mobile use a functional accessible menu or wrap/stack links, not hidden unreachable routes.
- A primary call-to-action **«Написать статью»** visible to a user with article-writing permission; a visitor sees **«Войти»** / **«Зарегистрироваться»**.
- Page title and short explanatory subtitle where it helps orient the user.
- Article card with title, category, author, date, excerpt, optional cover, and linked readable hit area.
- Button variants: primary / secondary / quiet / danger; consistent loading/disabled/hover/focus states.
- Input/select/textarea, tags, searchable filters, pagination, status badges, alerts, error descriptions, empty states, and confirmation dialog.
- Notification badge based on real unread counts, without any fabricated values.
- Server-rendered validation errors adjacent to relevant fields, with a concise top-level summary for multi-field errors.

Actions must use semantic HTML (`<form>`, `<button>`, `<a>`, headings, labels). Do not make a decorative `<div>` behave like a button unless equivalent accessibility and keyboard support are implemented.

## 3. Page-by-page redesign

### 3.1 Home / article feed — first priority

Goal: users should understand the product and find something interesting to read in seconds.

Desktop layout:

```text
[BRAND]  Статьи  Мои статьи*  Модерация*  Уведомления*       [Написать статью*] [Профиль / Войти]
-----------------------------------------------------------------------------------------------
[Корпоративный блог]                                  [Search________________________________]
Новости, идеи и опыт нашей команды                    [Все темы v] [Новые сначала v]

[Featured latest published article (wide card with actual title and excerpt)]

[Article card]                [Article card]              [Article card]
[Article card]                [Article card]              [Article card]

[Pagination / next page]
```

The star marks role-dependent elements, **not** literal UI labels. For mobile, cards become a single column, filters stack, nav remains reachable. Feature card is derived from an eligible published article; no new `is_featured` database field. If no articles exist, show a useful Russian empty-state message (not empty white space).

Acceptance points:
- Search, tags, category filters and pagination still work, and selected values remain visible after navigation.
- Render title, author/category/date from actual stored data; do not use placeholder content.
- Show only published, non-deleted items; cover images from uploaded media when supported or locally styled CSS placeholders otherwise.
- A full card or clearly labeled title link opens the detail page. Distinguishable focus and hover states.

### 3.2 Article reading page

- Reading column max ~760px, readable title/metadata, clear category, attractive heading and paragraph spacing, safe Markdown formatting already supported by current project.
- Show author name, date, reactions and comment count when real values exist.
- Place reaction controls and comments beneath the article, with clear comment composer for signed-in readers and a straightforward login prompt for visitors.
- Threaded comments should visually show replies; keep complaint/report action understated but discoverable.
- Article attachments must remain usable, with proper download and accessible file text.
- Do not expose article edit, moderate or delete controls to visitors lacking permission; editor and owner see only actions they actually can execute.
- If an article has been soft-deleted or hidden, return existing authorized behavior; never leak the body through an alternate read or search path.

### 3.3 Registration and login

- Centered, narrow card or form with friendly copy and a clearly labeled alternate link (login ↔ registration).
- Explicit field labels, password fields, clear field-level validation messages, and keyboard navigation.
- Do **not** weaken existing PBKDF2 hashing, sessions, CSRF, unique login validation or new user permissions.
- On success, redirect clearly to the existing user workflow, with an informative confirmation in Russian.

### 3.4 My Articles / author workspace

- This is the user's home for managing their work. Add clear page heading, **«Создать статью»** action, status filters (`Черновики`, `На модерации`, `Требуют правок`, `Опубликованные`, `Архив`) based on actual statuses, plus a unified list/table/card presentation.
- Each article item shows title, status, last modified date (if stored), category, and available contextual actions (`Просмотреть`, `Редактировать`, `Удалить`) conditional on status/permission.
- For empty results show a helpful action to create a new article; for rejected/needs-revision articles display a prompt to read editor remarks.
- **Soft deletion must remain prominent enough to find but visually secondary and clearly destructive.** Keep the existing confirmation and CSRF-backed POST; no client-side disappearance before successful server response.
- Never show deleted articles in normal lists.

### 3.5 Article editor — second priority

- Present creation as a simple flow: **заголовок → содержание → рубрика/теги → вложения → сохранить/отправить**.
- Make body input comfortably tall and resizable. Preserve existing Markdown/formatting semantics; if a preview is added, it must use the same safe rendering rules as article detail.
- Show an honest autosave indicator (`Сохранение…`, `Сохранено`, `Не удалось сохранить`) only reflecting actual state; do not fake a successful save.
- Visually separate **«Сохранить черновик»** (secondary) from **«Отправить на модерацию»** (primary). Disable inappropriate actions while submission is in progress, and show server-side validation errors without erasing typed content.
- Show moderation status and existing editor remarks when relevant.
- Keep media upload and delete, category/tag selection, and the existing article deletion path with confirmation.
- Make actions reachable at 360px without sticky elements covering the text area or browser controls.

### 3.6 Editor moderation dashboard

- Clear tabs/filters for article submissions and comment complaints (if already implemented); separate these concepts visually.
- Article queue shows title, author, submission date, priority and status with real data; the active item opens a reading panel/page.
- Approval is a clear positive action. Return for revision asks for a remark and validation. Feedback must identify which article was processed and where the editor can go next.
- Preserve sorting, priority changes, notifications and all moderation permissions.
- Deleted articles must not reappear in queue or remain actionable from a stale page.

### 3.7 Notifications and admin area

- Notifications: readable list with timestamps and meaningful differentiation (article submitted / approved / revision / complaint outcome), all based on existing notification records. Empty state when none; do not invent read/unread state if the backend does not support it.
- Admin: tidy sections for categories, users/roles/permissions and reporting. Do not merge editor moderation rights into admin by default; the original system separates the roles.
- Reports: present actual metrics in legible cards/tables; avoid fabricated chart datasets, unused controls, or hard-coded KPIs.

## 4. User experience details

- A user can always tell **where they are** (active nav item, page heading, breadcrumbs only if useful) and **what to do next** (one main call-to-action per primary page).
- Every form has clear submit feedback and preserves prior input on validation failure when safe.
- Confirmation UI explains irreversible *visibility* effect of a soft deletion without falsely claiming physical database erasure.
- Avoid alert storms, automatic modal popping and confusing double submissions.
- Where asynchronous behavior exists (autosave), communicate errors and success accurately; server remains authoritative.
- Provide correct empty states for search, notifications, My Articles, moderation queue and comments.
- Use Russian for all UI copy, including default errors and empty states. Internal status keys, class names and tests remain English.

## 5. Accessibility and responsive acceptance

Test at **360px, 768px and 1280px** widths; do not rely on device-specific CSS assumptions. Requirements:

- No horizontal overflow at 360px; navigation/action buttons remain reachable.
- Inputs and touch targets generally >=44px in hit height where practical; text does not clip.
- Keyboard navigation and visible `:focus-visible`; no focus traps in menus/dialogs; if a confirmation dialog is used, correctly manage focus and Escape/cancel behavior.
- Sufficient contrast (WCAG AA-level target for standard text); do not rely on color alone to convey a moderation or deletion status.
- Proper labels, headings, landmarks, `aria-live` feedback where useful; errors linked to fields.
- Images with informative alt text where meaningful, decorative graphics marked appropriately.
- Respect `prefers-reduced-motion` if any animations are introduced.
- Test content with long Russian article titles, multi-paragraph text and narrow viewports.

## 6. Delivery plan for Codex

**Step 0 — audit current presentation.** Inspect `omis_blog/web.py`, `omis_blog/site.css`, `omis_blog/presentation.py`, `omis_blog/infrastructure.py`, current route tests, `docs/uml_name_mapping.md`, original UML and existing seed content. Write `docs/ui_ux_stage2_baseline.md` describing current pages, problems found and preserved paths. If browser screenshots are possible, capture before images at 360 and 1280px.

**Step 1 — design system and global navigation.** Introduce tokens, shared components, header, layout containers, buttons, forms, focus and empty-state patterns. Keep all existing routes functional.

**Step 2 — reading experience.** Redesign home/feed and article detail, with real data, search/filter/pagination, comment/reaction controls. Test mobile and desktop.

**Step 3 — writing experience.** Redesign login/register, My Articles and editor; retain autosave, moderation status, editor remarks and soft deletion.

**Step 4 — management experience.** Redesign moderation, notifications and admin, maintaining role separation and real analytics.

**Step 5 — polish and verification.** Accessibility, responsive bugs, Russian text review, regression tests and visual before/after comparison. Update README with screenshots/usage if appropriate, `docs/test_matrix.md` and `docs/decisions.md`. Only update UML mapping if files/classes/methods truly move; fix any existing wrong source-file references after verifying the code.

## 7. Regression and acceptance

Use the current project commands, not assumptions about installed packages. At a minimum:

```bash
python3 -m pytest -q
ruff check omis_blog scripts tests
mypy omis_blog scripts
python3 scripts/check_english_identifiers.py
```

If CLI path/syntax differs, use the actual project command from README and report it. Do not blindly edit check scripts to make failing checks pass.

Smoke-test representative existing workflows on the actual app:

1. Public visitor can read all five seeded published articles and filter/search them.
2. Register → create draft → save → sign out/in → edit → submit → editor sees ticket → approves → article appears publicly.
3. Author can delete a draft, submitted article or published article using confirmation; deleted item disappears from all normal lists, search and moderation.
4. Editor receives new-article notifications, reviews content and can request changes; admin remains independent by default.
5. Reader can react, comment, reply and report; complaint moderation remains functional.
6. Non-owner cannot edit/delete another author's content; unauthenticated visitor cannot post; CSRF protections remain effective.
7. All existing UML and database roundtrip tests still pass; `PRAGMA integrity_check` is `ok` and foreign-key violations are zero.

**Screenshots to deliver:** desktop 1280px and mobile 360px for feed, article detail, editor, My Articles, moderation dashboard and login/registration (12+ images as appropriate). If automated screenshots are not possible, state exactly why and provide manual visual verification instructions rather than claiming they were captured.

**Definition of done:** All routes and features still work; all tests pass; UI is visually consistent and responsive; Russian UI copy is polished; code identifiers remain English; no seed data lost or duplicate articles created; deleted content stays hidden; current core UML remains intact.

## 8. Mandatory final report from Codex

Report: changed files; before/after UX improvements per screen; components introduced; tests and exact results; browser viewport sizes and screenshot locations; unresolved issues; **confirmation that no database migration or changes to base UML contracts occurred** (or explicitly explain any exception). Do not state that user acceptance is complete before an actual manual review.

---

## Copy-paste instruction for Codex

> Read `OMIS_UI_UX_STAGE_2.md`, the current project files, and the UML source/reference documentation. Implement this **presentation-only, incremental UI/UX redesign** in steps 0–5, preserving all working registration, authoring, moderation, notifications, publishing and soft deletion paths. Keep the existing Python WSGI/SQLite architecture, fully English code identifiers, and Russian user-facing text. Run the full test suite after each step. Provide screenshots at 360px and 1280px, an exact verification report, and updated documentation. Do not create fake controls or simplify away UML components.
