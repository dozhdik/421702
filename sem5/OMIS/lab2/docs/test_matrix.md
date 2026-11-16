# Матрица сценариев и тестов

Итерация из `задание/`: `tests/test_upgrade.py` проверяет регистрацию, нормализацию/уникальность логина, ротацию сессии, права нового автора, черновик, повторное открытие, модерацию и замечание после нового входа. Второй тест проверяет пять полных статей, связи/индексы/протоколы, видимость в ленте, сохранность ручной правки после повторного seed и целостность SQLite. Старые сценарии сохранены в `tests/test_web.py`, `tests/test_controllers.py`, `tests/test_storage.py`. `scripts/check_english_identifiers.py` входит в локальные проверки README.

Фактическая приёмка 2026-11-09: `pytest` — 23 теста успешно; `ruff check omis_blog scripts tests` — без замечаний; `mypy` — 11 исходных файлов без ошибок (`mypy omis_blog scripts` — 16 файлов); проверка английских Python-идентификаторов — успешно. Локальный HTTP smoke-test: `/` 200 (6 карточек: прежняя и 5 новых), `/register` 200, `/assets/site.css` 200; при прямом запуске создано 5 seed-статей. Firefox headless снимки при ширине 1280 и 360 px проверены визуально. Рабочая SQLite БД: `integrity_check=ok`, 0 нарушений FK, 4 исходных входа работают, имена таблиц и столбцов ASCII.

Дополнение 2026-11-11: `tests/test_article_delete.py` проверяет мягкое удаление во всех шести статусах, кнопку и подтверждение, CSRF, право владельца и отдельное право на чужую статью, закрытие активной заявки, исчезновение из ленты, поиска, личного кабинета и очереди, сохранность связанных строк, запрет повторной записи и результат после перезапуска и повторного наполнения. Текущее число тестов: 31.

Источник: [отчёт](reference/ОМИС%20Лаба%201%20Отчёт.pdf), BPMN стр. 7–8, use-case стр. 9, sequence стр. 10, UI-состояния стр. 15, макеты стр. 15–17.

| Сценарий | Источник | Ожидаемая проверка | Тест |
| --- | --- | --- | --- |
| Вход, ошибка пароля, заблокированный аккаунт, выход | C/G | сессия и серверный RBAC | `tests/test_auth.py::test_password_active_status_and_server_rights`, `tests/test_web.py::test_role_scenarios_in_browser` |
| Создание и неполное сохранение черновика | B/C/H.2 | запись сохраняется после перезапуска | `tests/test_domain.py::test_incomplete_draft_is_allowed_but_not_submittable`, `tests/test_web.py::test_role_scenarios_in_browser` |
| Правка только своего черновика, теги, рубрика, оформление, медиа | C/H.2 | все поля и связи сохраняются | `tests/test_web.py::test_editor_media_autosave_search_archive_and_moderation`, `tests/test_storage.py::test_article_tags_are_persistent` |
| Автосохранение изменённого черновика | G/H.2 | статус и дата сохраняются | `tests/test_web.py::test_editor_media_autosave_search_archive_and_moderation` |
| Отправка с валидацией обязательных полей | B | ошибка пустого поля или заявка в очереди | `tests/test_controllers.py::test_submission_rejects_incomplete_draft_without_ticket`, `tests/test_controllers.py::test_publication_rejection_resubmission_and_index` |
| Уведомление редактора о новой заявке | B | сохранённый адресный объект уведомления | `tests/test_controllers.py::test_publication_rejection_resubmission_and_index` |
| Очередь, фильтр, приоритет, просмотр вложений | B/H.3 | реальные заявки в порядке приоритета | `tests/test_web.py::test_editor_media_autosave_search_archive_and_moderation` |
| Возврат статьи с замечанием, уведомление автора, доработка и повторная отправка | B/C | допустимые переходы и сохранённое замечание | `tests/test_controllers.py::test_publication_rejection_resubmission_and_index` |
| Одобрение, немедленная публикация, протокол, индекс, лента, уведомление | B/C | атомарный наблюдаемый результат | `tests/test_controllers.py::test_publication_rejection_resubmission_and_index`, `tests/test_web.py::test_role_scenarios_in_browser` |
| Архив/снятие с публикации и запрет чтения | описание стр. 2–3 | материал не виден в ленте | `tests/test_domain.py::test_all_transitions_are_enforced`, `tests/test_web.py::test_editor_media_autosave_search_archive_and_moderation` |
| Публичная лента, сортировка, пагинация и фильтр рубрики | C/H.1 | только опубликованные записи | `tests/test_controllers.py::test_feed_filters_and_pagination_exclude_drafts`, `tests/test_web.py::test_role_scenarios_in_browser` |
| Поиск по тексту, автору, рубрике, тегу | C/A.6 | используется сохранённый индекс | `tests/test_controllers.py::test_publication_rejection_resubmission_and_index`, `tests/test_web.py::test_editor_media_autosave_search_archive_and_moderation` |
| Чтение, учёт просмотра, комментарий, ответ в ветке | C/H.4 | parent ID, публичная видимость | `tests/test_web.py::test_role_scenarios_in_browser`, `tests/test_web.py::test_third_complaint_and_admin_rights` |
| Реакция и подсчёт | C/H.4 | счётчик по сохранённым реакциям | `tests/test_web.py::test_role_scenarios_in_browser`, `tests/test_controllers.py::test_report_counts_persisted_activity` |
| Первая и вторая уникальные жалобы | D, стр. 10 | комментарий остаётся видимым | `tests/test_controllers.py::test_complaint_threshold_unique_and_both_decisions` |
| Третья уникальная жалоба и повторная жалоба того же лица | D, стр. 10 | скрытие и тикет, без накрутки порога | `tests/test_controllers.py::test_complaint_threshold_unique_and_both_decisions`, `tests/test_web.py::test_third_complaint_and_admin_rights` |
| Подтверждение нарушения, удаление, предупреждение и сообщение заявителям | D/H.3 | комментарий скрыт, уведомления сохранены | `tests/test_controllers.py::test_complaint_threshold_unique_and_both_decisions` |
| Отклонение жалобы, восстановление и сообщение заявителям | D/H.3 | комментарий виден, уведомления сохранены | `tests/test_controllers.py::test_complaint_threshold_unique_and_both_decisions` |
| CRUD рубрик, роли и права | C | только администратор | `tests/test_web.py::test_role_scenarios_in_browser`, `tests/test_web.py::test_third_complaint_and_admin_rights` |
| Отчёт за период | C | публикации, комментарии, реакции, просмотры из БД | `tests/test_controllers.py::test_report_counts_persisted_activity`, `tests/test_web.py::test_role_scenarios_in_browser` |
| Четыре команды и откат | E.2 | состояние до/после и восстановление | `tests/test_controllers.py::test_four_commands_restore_prior_state` |
| Две стратегии, подмена через DI | E.2 | одинаковый контракт, разное решение | `tests/test_controllers.py::test_strategy_and_report` |
| Все UML-классы, поля, методы и связи | A/E | автоматический coverage/roundtrip | `tests/test_uml_coverage.py`, `tests/test_storage.py::test_every_entity_roundtrips_across_restart` |
| Фабрики, контейнер, конфигуратор, точка входа | E.4/E.5 | создают реальные связанные объекты | `tests/test_infrastructure.py::test_configurator_creates_and_links_all_components` |
| Чистый запуск и данные после рестарта | README §8 | UI работает без ручной БД | `tests/test_storage.py::test_every_entity_roundtrips_across_restart`, `tests/test_web.py::test_role_scenarios_in_browser` |

## UI/UX Stage 2 — промежуточная проверка

| Проверка | Результат |
| --- | --- |
| Полный pytest после этапов 0, 1, 2, 3 и 4 | По 31 тесту пройдено на каждом checkpoint |
| Лента, статья, редактор, мои статьи, модерация и вход | Снимки Firefox при ширине 360 и 1280 px в `docs/screenshots/stage2/after/` |
| Ручная проверка клавиатурой, контраста и ширины 768 px | Ещё требуется |
