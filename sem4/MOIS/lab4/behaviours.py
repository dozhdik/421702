"""
Модуль поведений агентов МАС управления курсовым проектом.

Используемые типы поведений (требование лабораторной — минимум 2):
- OneShotBehaviour: однократная подача темы студентом
- CyclicBehaviour: циклическая обработка входящих сообщений (студент, координатор)
- PeriodicBehaviour: периодический контроль дедлайнов координатором
- FSMBehaviour: конечный автомат рецензирования руководителя

Коммуникация: FIPA-совместимые метаданные (performative, protocol, ontology, language)
через msg.set_metadata() и фильтрация через MessageTemplate при add_behaviour().
"""

import asyncio
import logging
from spade.behaviour import (
    OneShotBehaviour,
    CyclicBehaviour,
    PeriodicBehaviour,
    FSMBehaviour,
    State,
)
from spade.message import Message

logger = logging.getLogger("coursework_mas")

# Имена состояний FSM руководителя
STATE_WAIT = "STATE_WAIT"
STATE_REVIEW = "STATE_REVIEW"
STATE_APPROVE = "STATE_APPROVE"
STATE_REJECT = "STATE_REJECT"


# ============================================================
# Поведения StudentAgent
# ============================================================


class SubmitTopicBehaviour(OneShotBehaviour):
    """
    OneShotBehaviour — выполняется однократно при старте агента.
    Студент отправляет заявку на тему курсового проекта координатору.
    """

    async def on_start(self):
        logger.info("[Student] Подготовка заявки на тему курсового проекта...")

    async def run(self):
        # Небольшая задержка, чтобы все агенты успели подключиться
        await asyncio.sleep(3)

        msg = Message(to=self.agent.config["coordinator_jid"])
        msg.body = "ЭТАП 1: Тема 'Разработка многоагентной системы на SPADE'"
        msg.set_metadata("performative", "request")
        msg.set_metadata("protocol", "coursework-management")
        msg.set_metadata("ontology", "topic-submission")
        msg.set_metadata("language", "Russian")

        await self.send(msg)
        logger.info("[Student] Заявка на тему отправлена координатору.")

    async def on_end(self):
        logger.info("[Student] Поведение SubmitTopic завершено.")


class StudentResponseHandler(CyclicBehaviour):
    """
    CyclicBehaviour — циклически ожидает входящие сообщения.
    Обрабатывает ответы от координатора и переходит к следующему этапу.

    Фильтрация: MessageTemplate с performative='inform' назначается
    при добавлении поведения в agents.py, чтобы не перехватывать
    чужие сообщения (например, request от других агентов).
    """

    STAGES = {
        2: "Черновик введения и план работы подготовлены",
        3: "Основная часть и эксперименты завершены",
        4: "Финальная версия отчёта готова к защите",
    }

    async def run(self):
        msg = await self.receive(timeout=15)
        if msg is None:
            return

        body = msg.body or ""
        sender = str(msg.sender).split("/")[0]
        logger.info(f"[Student] Получено от {sender}: {body}")

        # Реагируем на одобрение этапа
        if "одобрен" in body.lower() or "утверждён" in body.lower():
            self.agent.current_stage += 1
            logger.info(f"[Student] Этап {self.agent.current_stage - 1} принят. Переход к этапу {self.agent.current_stage}.")

            if self.agent.current_stage > 4:
                logger.info("[Student] ВСЕ ЭТАПЫ ПРОЙДЕНЫ. Курсовой проект защищён!")
                self.agent.project_done = True
                self.kill()
                return

            # Отправляем отчёт по следующему этапу
            stage_desc = self.STAGES.get(self.agent.current_stage, "Неизвестный этап")
            await asyncio.sleep(1.5)

            report = Message(to=self.agent.config["coordinator_jid"])
            report.body = f"ЭТАП {self.agent.current_stage}: {stage_desc}"
            report.set_metadata("performative", "request")
            report.set_metadata("protocol", "coursework-management")
            report.set_metadata("ontology", "stage-report")
            report.set_metadata("language", "Russian")

            await self.send(report)
            logger.info(f"[Student] Отчёт по этапу {self.agent.current_stage} отправлен координатору.")

        elif "напоминание" in body.lower() or "дедлайн" in body.lower():
            logger.info("[Student] Принято напоминание о дедлайне. Продолжаю работу.")


# ============================================================
# Поведения SupervisorAgent — FSMBehaviour
# ============================================================


class SupervisorReviewFSM(FSMBehaviour):
    """
    FSMBehaviour — конечный автомат рецензирования руководителя.
    Состояния: WAIT -> REVIEW -> APPROVE/REJECT -> WAIT (цикл).
    Состояния и переходы регистрируются в agents.py при создании поведения.
    """

    async def on_start(self):
        logger.info("[Supervisor/FSM] Конечный автомат рецензирования запущен.")

    async def on_end(self):
        logger.info("[Supervisor/FSM] Конечный автомат завершён.")


class WaitForSubmissionState(State):
    """Начальное состояние FSM: ожидание материалов на проверку."""

    async def run(self):
        msg = await self.receive(timeout=10)
        if msg:
            self.agent.current_submission = msg.body
            self.agent.submission_sender = str(msg.sender).split("/")[0]
            logger.info(f"[Supervisor/FSM] Получены материалы на проверку: {msg.body[:80]}")
            self.set_next_state(STATE_REVIEW)
        else:
            # Остаёмся в состоянии ожидания
            self.set_next_state(STATE_WAIT)


class ReviewState(State):
    """Состояние анализа: руководитель проверяет материалы."""

    async def run(self):
        logger.info("[Supervisor/FSM] Анализ полученных материалов...")
        await asyncio.sleep(2)
        # Логика принятия решения (в демо — всегда одобряем)
        self.agent.review_decision = "approve"
        logger.info("[Supervisor/FSM] Анализ завершён.")

        if self.agent.review_decision == "approve":
            self.set_next_state(STATE_APPROVE)
        else:
            self.set_next_state(STATE_REJECT)


class ApproveState(State):
    """Состояние одобрения: отправка подтверждения координатору."""

    async def run(self):
        logger.info("[Supervisor/FSM] Решение: УТВЕРЖДЕНО.")

        reply = Message(to=self.agent.config["coordinator_jid"])
        reply.body = f"Этап утверждён руководителем: {self.agent.current_submission[:60]}"
        reply.set_metadata("performative", "inform")
        reply.set_metadata("protocol", "coursework-management")
        reply.set_metadata("ontology", "review-approved")
        reply.set_metadata("language", "Russian")

        await self.send(reply)
        logger.info("[Supervisor/FSM] Результат рецензии отправлен координатору.")
        # Возвращаемся в ожидание следующего этапа
        self.set_next_state(STATE_WAIT)


class RejectState(State):
    """Состояние отклонения: запрос доработки у студента."""

    async def run(self):
        logger.info("[Supervisor/FSM] Решение: ОТКЛОНЕНО. Требуется доработка.")

        reply = Message(to=self.agent.config["coordinator_jid"])
        reply.body = f"Этап отклонён. Доработать: {self.agent.current_submission[:60]}"
        reply.set_metadata("performative", "inform")
        reply.set_metadata("protocol", "coursework-management")
        reply.set_metadata("ontology", "review-rejected")
        reply.set_metadata("language", "Russian")

        await self.send(reply)
        self.set_next_state(STATE_WAIT)


# ============================================================
# Поведения CoordinatorAgent
# ============================================================


class CoordinatorRequestHandler(CyclicBehaviour):
    """
    CyclicBehaviour — обработка запросов (performative='request') от студента.
    Координатор пересылает материалы руководителю на рецензию.

    Фильтрация: MessageTemplate с performative='request' назначается
    при add_behaviour в agents.py.
    """

    async def run(self):
        msg = await self.receive(timeout=10)
        if msg is None:
            return

        sender = str(msg.sender).split("/")[0]
        body = msg.body or ""
        logger.info(f"[Coordinator] Получен запрос от {sender}: {body[:80]}")

        # Пересылаем материалы руководителю
        forward = Message(to=self.agent.config["supervisor_jid"])
        forward.body = body
        forward.set_metadata("performative", "request")
        forward.set_metadata("protocol", "coursework-management")
        forward.set_metadata("ontology", msg.get_metadata("ontology") or "stage-report")
        forward.set_metadata("language", "Russian")

        await self.send(forward)
        logger.info("[Coordinator] Материалы переданы руководителю на рецензию.")


class CoordinatorInformHandler(CyclicBehaviour):
    """
    CyclicBehaviour — обработка результатов рецензии (performative='inform')
    от руководителя. Координатор пересылает решение студенту.

    Фильтрация: MessageTemplate с performative='inform' назначается
    при add_behaviour в agents.py.
    """

    async def run(self):
        msg = await self.receive(timeout=10)
        if msg is None:
            return

        sender = str(msg.sender).split("/")[0]
        body = msg.body or ""
        logger.info(f"[Coordinator] Получен результат рецензии от {sender}: {body[:80]}")

        # Пересылаем решение студенту
        forward = Message(to=self.agent.config["student_jid"])
        if "утверждён" in body.lower():
            forward.body = f"Одобрено: {body}"
        else:
            forward.body = f"Отклонено: {body}"
        forward.set_metadata("performative", "inform")
        forward.set_metadata("protocol", "coursework-management")
        forward.set_metadata("ontology", "coordinator-decision")
        forward.set_metadata("language", "Russian")

        await self.send(forward)
        logger.info("[Coordinator] Решение передано студенту.")


class DeadlineCheckerBehaviour(PeriodicBehaviour):
    """
    PeriodicBehaviour — периодическая проверка дедлайнов (каждые N секунд).
    Координатор отправляет напоминания студенту о приближающихся сроках.
    """

    async def on_start(self):
        self.check_count = 0
        logger.info("[Coordinator/Deadline] Периодический контроль дедлайнов запущен (период: 8 сек).")

    async def run(self):
        self.check_count += 1
        logger.info(f"[Coordinator/Deadline] Проверка #{self.check_count}. Мониторинг сроков...")

        # Каждый 2-й цикл отправляем напоминание
        if self.check_count % 2 == 0:
            reminder = Message(to=self.agent.config["student_jid"])
            reminder.body = "Напоминание: дедлайн текущего этапа приближается!"
            reminder.set_metadata("performative", "inform")
            reminder.set_metadata("protocol", "coursework-management")
            reminder.set_metadata("ontology", "deadline-reminder")
            reminder.set_metadata("language", "Russian")
            await self.send(reminder)
            logger.info("[Coordinator/Deadline] Напоминание о дедлайне отправлено студенту.")
