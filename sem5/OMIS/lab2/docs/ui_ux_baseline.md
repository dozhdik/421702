# UI, authentication, and data baseline before the upgrade

Checked against the repository and `blog.sqlite` before editing code. The original `README.md`, `docs/uml_coverage.md`, `docs/test_matrix.md`, `docs/decisions.md`, and the PDF in `docs/reference/` remain the requirements baseline. The new files in `задание/` override naming conventions and add registration, five articles, and a revised UI.

## Existing application

The application runs on Python standard-library `wsgiref` and `sqlite3`. It has a single WSGI router in `omis_blog/web.py`, domain classes in `domain.py`, four repositories in `storage.py`, five controllers in `controllers.py`, view interfaces/adapters in `presentation.py`, DI in `infrastructure.py`, and deterministic demo seeding in `scripts/seed_demo.py`.

Current routes: `/`, `/login`, `/logout`, `/article/<id>`, `/article/save`, `/article/<id>/comment`, `/article/<id>/react`, `/article/<id>/report`, `/article/<id>/status`, `/editor/new`, `/editor/<id>`, `/moderation`, `/moderation/article/<id>`, `/moderation/complaint/<id>`, `/moderation/priority/<id>`, `/admin`, `/admin/rubric`, `/admin/role`, `/admin/permission`, `/admin/report`, `/notifications`, `/media/<id>`, and `/media/<id>/delete`.

Login uses PBKDF2 password hashes, a SQLite-backed session, CSRF token, and role permissions. Four demo accounts exist. New-user registration and an author-only article list do not exist. The current feed is publicly readable; this is existing behavior, so the upgrade must keep it unless the user changes the requirement.

The current HTML is generated in `web.py` with a small inline stylesheet. Navigation, cards, forms, and article text have basic function but limited hierarchy, mobile layout, error placement, and reusable presentation components. There is no separate static CSS file. Existing UI-state classes and view adapters are connected through the configurator. The article body is plain escaped text with line breaks; Markdown headings are not rendered.

## Baseline checks and database

- `python3 -m pytest -q`: **20 passed** before edits.
- `blog.sqlite`: `PRAGMA integrity_check = ok`; 4 accounts, 3 articles, 2 comments, 2 complaints, 1 published index, 1 publication record. The live schema has Cyrillic table and column names.
- SQLite backup created at `backups/blog-before-english-upgrade.sqlite` using the SQLite backup API before any migration. The backup is ignored by Git to avoid publishing user data.

## Planned changes

Rename all runtime identifiers and SQL schema with a tested migration; keep all UML entities and contracts. Add self-service author registration and `My Articles`. Import five complete JSON articles through the existing seeder. Improve the current WSGI views and CSS while retaining every existing action.
