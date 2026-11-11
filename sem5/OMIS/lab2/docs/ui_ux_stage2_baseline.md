# UI/UX Stage 2 — baseline audit

**Date:** 2026-11-11. **Scope:** presentation-only audit before the editorial redesign. No UML source contract or SQLite field was changed during this audit.

## Existing implementation

- `omis_blog/web.py` is the single WSGI presentation layer. It owns route dispatch, session loading, CSRF validation, role checks, page layout and per-page HTML rendering. The existing domain and application setup remain under `domain.py`, `controllers.py`, `storage.py`, `presentation.py` and `infrastructure.py`.
- `omis_blog/site.css` is local and offline, but had become a compressed collection of one-line rules and successive overrides. It already had a responsive feed grid, article covers, editor form, and basic keyboard focus outline.
- `presentation.py` still provides the UML E.3 view contracts and concrete Feed, Editor, Moderator, Article Detail and Report views. `WebApp` updates their A.7 state objects per session.
- `docs/uml_name_mapping.md`, `docs/uml_coverage.md`, the original PDF and diagrams under `docs/reference/diagrams/` remain the naming and model references. The presentation work adds no UML class and does not remove an existing interface.

## Route and feature inventory to preserve

| Route or flow | Existing behavior |
|---|---|
| `/`, `/article/<id>` | Public published feed, text search, author/category/tag filters, pagination, article detail, safe Markdown subset, real counters, comments, replies, reactions and complaints |
| `/login`, `/register`, `/logout` | PBKDF2 login, self-registration, rotated sessions, logout invalidation, CSRF and role-derived navigation |
| `/my-articles`, `/editor/<id>`, `/article/save` | Author-only list, draft and revision editing, category/tags/media/formatting, 30-second autosave, submit for moderation, remarks, soft delete |
| `/moderation`, `/moderation/article/<id>`, `/moderation/priority/<id>`, `/moderation/complaint/<id>` | Article queue, priority, approval or return with remark, complaint threshold and decisions |
| `/notifications` | Existing user notification records and timestamps |
| `/admin`, `/admin/*` | Category management, role and permission assignment, activity reports |
| `/media/<id>`, `/media/<id>/delete` | Permission-checked attachment access and owner deletion |

## Baseline usability findings

- The feed has real article content and CSS covers, but the visual hierarchy is repeated and all filters appear at the same level. There is no featured article treatment or explicit sort selector; none will be added unless backed by working behavior.
- The shared header lacks active-page feedback and a clear role-aware writing action. Notification records are real, but the header has no unread count.
- Reading pages and management pages share generic article/form styling. Comment replies do not have a strong visual nesting cue; attachment links are text only.
- Registration/login and author/editor forms are usable but compact and use the same undifferentiated field/button treatment. Autosave reports only a terminal success/failure string.
- Moderation, notifications and admin use long ungrouped streams of forms. Empty states exist for some lists but not all.
- Current HTML uses server-side escaping and POST+CSRF for changes; those safeguards must stay in place. The confirmation for article soft deletion is a browser confirmation and is retained.

## Before screenshots

- Feed at 360 px: [feed-360.png](screenshots/stage2/before/feed-360.png)
- Feed at 1280 px: [feed-1280.png](screenshots/stage2/before/feed-1280.png)

## Baseline verification

- `python3 -m pytest -q`: 31 passed.
- `ruff check omis_blog scripts tests`: clean.
- `mypy omis_blog scripts`: 16 source files, no issues.
- `python3 scripts/check_english_identifiers.py .`: no non-ASCII Python identifiers.
- The checkout initially lacked `задание/seed_articles.json`, which existing seed code and tests require. Restored the fixture from the five matching `seed_key` records in `blog.sqlite`, preserving the existing titles, summaries, full Markdown, categories, tags, dates and cover themes. This is a test/demo content fixture, not a runtime logic or schema change.
