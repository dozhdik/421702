# OMIS — verified documentation baseline for the next Codex iteration

> Scope: improvement of the existing corporate blog (UI/UX, self-service author registration, 5 full-length demo articles, English-only source identifiers). This baseline was derived from the user's `README.md`, `docs/uml_coverage.md`, `docs/test_matrix.md` and `docs/decisions.md`, not from a fresh execution of the implementation. **Treat any claim of implementation as unverified until you inspect and run the repository.**

## A. Actual reported architecture — do not assume FastAPI/SQLAlchemy

`docs/decisions.md` explicitly reports the local implementation uses **Python standard-library `wsgiref` and `sqlite3`**, without FastAPI or SQLAlchemy as runtime dependencies. Refine its existing HTML/CSS/JavaScript and WSGI routes unless code inspection reveals a deliberate framework change. Do not introduce a new backend framework merely to redesign the UI.

Reported existing locations:

| Area | Existing module(s) | Existing tests |
| --- | --- | --- |
| Domain models, 21 base UML entities, 6 UI states | `omis_blog/domain.py` | `tests/test_domain.py`, `tests/test_uml_coverage.py` |
| SQL storage and repositories | `omis_blog/storage.py` | `tests/test_storage.py` |
| Login, sessions, role/permission checks | `omis_blog/auth.py`, `omis_blog/web.py` | `tests/test_auth.py`, `tests/test_web.py` |
| Publication, moderation, feed, notifications, reporting | `omis_blog/controllers.py` | `tests/test_controllers.py` |
| Moderation strategies and commands | `omis_blog/patterns.py` | `tests/test_controllers.py` |
| Required presentation/view contracts | `omis_blog/presentation.py` | `tests/test_infrastructure.py`, `tests/test_uml_coverage.py` |
| DI, controller/view factories, system configurator | `omis_blog/infrastructure.py` | `tests/test_infrastructure.py` |
| Program entrypoint | `omis_blog/main.py` | `tests/test_infrastructure.py` |
| Browser/server flows | `omis_blog/web.py` | `tests/test_web.py` |
| Demo data | `scripts/seed_demo.py` | Repeat-run idempotence must be checked in source/tests |

These locations are **from the reports**; verify them against the actual repository before editing.

## B. What the old reports claim is already implemented

- 21 base UML entities, 6 UI state entities, 4 mandatory repositories, 5 controllers, 2 strategies, 4 commands, required view interfaces/concrete adapters, factories, DI container and app entrypoint are all marked `[x]` in `docs/uml_coverage.md`.
- Four demo roles/accounts already support login, and the test matrix lists password/active-account and server-side RBAC tests.
- Draft saving, 30-second-style autosave, editor review, resubmission, publish/index/feed, attachments, search, reactions, comments, complaints and reports have named tests.
- Complaint threshold is three **unique open complaints**, followed by editor confirmation/deletion or rejection/restoration.
- A user session is persisted in SQLite; **per-session feed/editor/moderation/view UI state is held in web-server memory**. Do not confuse that memory state with durable article drafts; confirm saving and refresh behavior.
- Approval immediately publishes; no scheduled publication/revision module/tenant isolation is in scope.
- Unchanged security/content constraints and existing user records take precedence over cosmetic improvements.

The reports do **not** demonstrate that anonymous sign-up already exists. They also do not provide a green test run in the current session. Check before implementing.

## C. Required decisions for this iteration

### C1. English-only programming identifiers — mandatory

The old UML coverage file lists **Cyrillic program identifiers** and `tests/test_uml_coverage.py` reportedly checks those exact public names. Rename source identifiers consistently to semantic English; do **not** preserve Cyrillic runtime aliases only to satisfy old tests. Update all tests to assert the **English** mapping of every original UML element; keep the original Russian UML names **only in mapping/reference documentation**, not as code symbols. Update `docs/uml_coverage.md` to point to the new names/files, and create an exhaustive `docs/uml_name_mapping.md` for 1:1 traceability.

Inspect Python, SQL table/column/index/constraint names, JavaScript, HTML attributes/selectors, CSS, serialized JSON/API keys and scripts. Perform **a database migration only if necessary** after introspecting the actual live schema. An English Python class name alone does not imply a Cyrillic SQL schema. If migration is needed, backup data and prove existing users, password hashes, article IDs and links survive.

### C2. Add self-service registration to the **existing** auth architecture

The existing auth + sessions + `User`/`UserAccount`/role/profile concepts must be reused. New author registrations need the permissions of an author and reader under the current role model, but never editor/admin rights. Use an atomic transaction, unique case-insensitive login, properly hashed passwords, CSRF/session protection, and server-owned `author_id`. A new author must be able to create, save, edit **their own** draft, submit it, view editor feedback and eventually read the approved article. Existing demo accounts keep working.

Make `My Articles` and `Write Article` discoverable in the UI only to authorized accounts. Anonymous visitors must **not** gain access to a previously private corporate feed without an explicit requirement. Registration itself may be available to unauthenticated users as requested.

### C3. Import five existing articles into **current** SQLite storage

Use accompanying `seed_articles.json`. Do not mock article cards or hardcode articles in HTML. Extend existing `scripts/seed_demo.py` (or its verified equivalent) to insert all five published articles, correctly linked to categories/tags/author/publication record/search index, with full content and stable `seed_key` identity. Use insert-if-missing and do **not** overwrite existing content. The seeder must remain idempotent. No external image service is required; local CSS cover artwork is acceptable.

### C4. UI redesign in the existing stack

Restructure HTML/CSS/JS for a reusable header, readable article cards, article detail page, registration and login, author editor, My Articles list, editor moderation dashboard, notifications and admin reports. Preserve every existing operation, and explicitly retain the required UML view interfaces and adapters from `presentation.py`. Avoid an unneeded SPA/Node stack switch. Keep user-facing UI labels/errors in Russian, and source/UI selector identifiers in English.

## D. Tests to keep and extend

Before modifying any code, run all existing tests and record failures. The reports name especially valuable tests:

- `tests/test_uml_coverage.py` — update to English class/field/method names without losing a single UML requirement.
- `tests/test_storage.py::test_every_entity_roundtrips_across_restart` — preserve persisted objects and relations through any migration.
- `tests/test_auth.py::test_password_active_status_and_server_rights` — preserve roles/security.
- `tests/test_controllers.py::test_publication_rejection_resubmission_and_index` — preserve article lifecycle.
- `tests/test_controllers.py::test_complaint_threshold_unique_and_both_decisions` — preserve complaint handling.
- `tests/test_web.py::test_role_scenarios_in_browser` and `tests/test_web.py::test_editor_media_autosave_search_archive_and_moderation` — preserve integrated workflows.
- `tests/test_infrastructure.py::test_configurator_creates_and_links_all_components` — preserve architecture/DI.

Add at least the following new tests: successful registration + persistent login; case-insensitive duplicate username; no privilege escalation or foreign draft edits; new-author-to-editor end-to-end publish/reject flow; five seeded articles discoverable in feed/search; seeding twice yields the same five records; original SQLite data survives migration; no Cyrillic program identifiers or SQL schema identifiers remain; UI mobile layout has no unusable navigation.

Do not claim green tests from the old reports. Report exact commands and actual pass/fail counts. Keep the code Python 3.11+.

## E. Suggested safe delivery order

1. Baseline: inspect source, current DB schema and tests; record green/red baseline, take a database backup.
2. English naming: full UML mapping; rename implementation and update static/behavioral tests, DI, storage and web layer; migrate DB **only if required**, with verification.
3. Registration + My Articles: complete and test role-sensitive user workflow.
4. Five published demo articles: import, index, persistence and idempotence tests.
5. UI/UX: responsive pages, article readability, accessible forms, retain moderation/comments/reactions/notifications/admin.
6. Acceptance: full tests, lints/type checks, naming checks, manual browser flow; update original README and documentation.

**Stop conditions:** a failing migration, lost article/user, broken authorization, fewer UML elements than before, or missing existing core workflow is a blocker. Restore integrity before further UI changes.

## F. Task handoff

Read `ENGLISH_CODEBASE_POLICY.md`, `UPGRADE_UI_UX_AUTH_SEED.md`, this baseline, `seed_articles.json`, the repository's actual source/tests, its `docs/uml_coverage.md`, `docs/test_matrix.md`, `docs/decisions.md`, and the Russian UML PDF. Implement this iteration in the existing application. Do not claim completion until you have executed real tests and a registration → draft → moderation → publication walkthrough.
