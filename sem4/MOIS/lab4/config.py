"""
Конфигурация МАС: JID, пароли, параметры XMPP-сервера.

Все параметры загружаются из .env файла (или переменных окружения).
Если .env отсутствует — используются значения по умолчанию для localhost.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # XMPP-сервер (Prosody, ejabberd или публичный тестовый)
    XMPP_SERVER = os.getenv("XMPP_SERVER", "localhost")
    XMPP_PORT = int(os.getenv("XMPP_PORT", "5222"))

    # Агент-студент
    STUDENT_JID = os.getenv("STUDENT_JID", "student@localhost")
    STUDENT_PASS = os.getenv("STUDENT_PASS", "student123")

    # Агент-руководитель
    SUPERVISOR_JID = os.getenv("SUPERVISOR_JID", "supervisor@localhost")
    SUPERVISOR_PASS = os.getenv("SUPERVISOR_PASS", "supervisor123")

    # Агент-координатор
    COORDINATOR_JID = os.getenv("COORDINATOR_JID", "coordinator@localhost")
    COORDINATOR_PASS = os.getenv("COORDINATOR_PASS", "coordinator123")
