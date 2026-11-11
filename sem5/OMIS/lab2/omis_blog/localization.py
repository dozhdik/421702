"""Russian strings presented to users; internal identifiers remain English."""

from __future__ import annotations

STATUS_LABELS = {
    "draft": "Черновик",
    "in_moderation": "На модерации",
    "needs_revision": "Требует правок",
    "published": "Опубликовано",
    "archived": "Архив",
    "unpublished": "Снято",
    "visible": "Виден",
    "hidden": "Скрыт",
    "deleted": "Удалён",
    "new": "Новая",
    "confirmed": "Подтверждена",
    "dismissed": "Отклонена",
}

REACTION_LABELS = {"like": "Нравится", "helpful": "Полезно"}
ROLE_LABELS = {"Author": "Автор контента"}

MESSAGES = {
    "article_awaits_review": "Статья {article_id} ждёт модерации",
    "comment_removed_warning": "Ваш комментарий удалён после проверки жалоб",
    "article_published": "Статья опубликована",
    "article_needs_revision": "Статья требует правок: {remark}",
    "complaint_needs_review": "Жалоба на комментарий ждёт решения",
    "complaint_confirmed": "Нарушение подтверждено; комментарий удалён",
    "complaint_dismissed": "Нарушение не подтверждено; комментарий восстановлен",
}

ERROR_MESSAGES = {
    "timestamp_requires_timezone": "Укажите часовой пояс даты и времени.",
    "missing_complainant": "Не указан заявитель.",
    "article_missing_required_fields": "Нужны заголовок, содержание и рубрика.",
    "remark_required": "Замечание обязательно.",
    "comment_deleted": "Комментарий удалён.",
    "duplicate_complaint": "Вы уже отправили жалобу на этот комментарий.",
    "no_open_complaints": "Нет открытых жалоб.",
    "restore_blocked_by_strategy": "Комментарий нельзя восстановить.",
    "unknown_verdict": "Неизвестное решение.",
    "invalid_period_format": "Период: ГГГГ-ММ-ДД/ГГГГ-ММ-ДД.",
    "period_start_after_end": "Начало периода позже конца.",
    "command_not_executed": "Действие ещё не выполнено.",
    "invalid_full_name": "Укажите ФИО длиной от 2 до 120 символов.",
    "invalid_login": "Логин: от 3 до 40 латинских букв, цифр или символов . _ -.",
    "invalid_password_length": "Пароль должен содержать от 10 до 128 символов.",
    "password_mismatch": "Пароли не совпадают.",
    "login_taken": "Этот логин уже занят.",
    "invalid_credentials": "Неверный логин или пароль.",
    "too_many_attempts": "Слишком много попыток входа. Попробуйте через пять минут.",
    "author_profile_missing": "Профиль автора не найден.",
    "article_delete_denied": "Удалять можно только свои статьи или статьи с отдельным разрешением.",
    "article_deleted": "Статья удалена и больше не доступна для изменений.",
}


def message(key: str, **values: str) -> str:
    return MESSAGES[key].format(**values)


def error_message(code: str) -> str:
    return ERROR_MESSAGES.get(code, code)


def status_label(value: str) -> str:
    return STATUS_LABELS.get(value, value)


def role_label(value: str) -> str:
    return ROLE_LABELS.get(value, value)
