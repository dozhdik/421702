"""
Модуль агентов МАС управления курсовым проектом.

Архитектура: 3 агента (требование лабораторной):
- StudentAgent: студент, подающий тему и отчёты по этапам
- SupervisorAgent: научный руководитель, рецензирующий материалы (FSM)
- CoordinatorAgent: координатор, маршрутизирующий сообщения и контролирующий дедлайны

Демонстрация MessageTemplate: каждое поведение привязывается к шаблону,
фильтрующему входящие сообщения по FIPA-метаданным (performative).
"""

import logging
from spade.agent import Agent
from spade.template import Template
from behaviours import (
    SubmitTopicBehaviour,
    StudentResponseHandler,
    SupervisorReviewFSM,
    WaitForSubmissionState,
    ReviewState,
    ApproveState,
    RejectState,
    CoordinatorRequestHandler,
    CoordinatorInformHandler,
    DeadlineCheckerBehaviour,
    STATE_WAIT,
    STATE_REVIEW,
    STATE_APPROVE,
    STATE_REJECT,
)

logger = logging.getLogger("coursework_mas")


class StudentAgent(Agent):
    """
    Агент-студент. Подаёт тему (OneShotBehaviour), затем циклически
    обрабатывает ответы координатора (CyclicBehaviour с шаблоном inform).
    """

    def __init__(self, jid, password, config):
        super().__init__(jid, password)
        self.config = config
        self.current_stage = 1
        self.project_done = False

    async def setup(self):
        logger.info(f"[StudentAgent] Агент {self.jid} запущен.")

        # OneShotBehaviour — подача темы (без шаблона, т.к. не принимает сообщений)
        self.add_behaviour(SubmitTopicBehaviour())

        # CyclicBehaviour — обработка ответов с фильтрацией по performative='inform'
        # MessageTemplate гарантирует, что это поведение получит только inform-сообщения
        inform_template = Template(metadata={"performative": "inform"})
        self.add_behaviour(StudentResponseHandler(), template=inform_template)


class SupervisorAgent(Agent):
    """
    Агент-руководитель. Использует FSMBehaviour для моделирования
    процесса рецензирования: WAIT -> REVIEW -> APPROVE/REJECT -> WAIT.

    FSM привязан к шаблону performative='request', чтобы получать
    только запросы на рецензию от координатора.
    """

    def __init__(self, jid, password, config):
        super().__init__(jid, password)
        self.config = config
        self.current_submission = ""
        self.submission_sender = ""
        self.review_decision = ""

    async def setup(self):
        logger.info(f"[SupervisorAgent] Агент {self.jid} запущен.")

        # Создаём FSMBehaviour и регистрируем состояния
        fsm = SupervisorReviewFSM()

        # Добавляем состояния FSM
        fsm.add_state(name=STATE_WAIT, state=WaitForSubmissionState(), initial=True)
        fsm.add_state(name=STATE_REVIEW, state=ReviewState())
        fsm.add_state(name=STATE_APPROVE, state=ApproveState())
        fsm.add_state(name=STATE_REJECT, state=RejectState())

        # Добавляем переходы между состояниями
        fsm.add_transition(source=STATE_WAIT, dest=STATE_WAIT)
        fsm.add_transition(source=STATE_WAIT, dest=STATE_REVIEW)
        fsm.add_transition(source=STATE_REVIEW, dest=STATE_APPROVE)
        fsm.add_transition(source=STATE_REVIEW, dest=STATE_REJECT)
        fsm.add_transition(source=STATE_APPROVE, dest=STATE_WAIT)
        fsm.add_transition(source=STATE_REJECT, dest=STATE_WAIT)

        # FSM привязан к шаблону: получает только request-сообщения
        request_template = Template(metadata={"performative": "request"})
        self.add_behaviour(fsm, template=request_template)


class CoordinatorAgent(Agent):
    """
    Агент-координатор. Маршрутизирует сообщения между студентом и руководителем.
    Два CyclicBehaviour с разными шаблонами:
    - request (от студента) -> пересылка руководителю
    - inform (от руководителя) -> пересылка студенту
    Плюс PeriodicBehaviour для контроля дедлайнов.
    """

    def __init__(self, jid, password, config):
        super().__init__(jid, password)
        self.config = config

    async def setup(self):
        logger.info(f"[CoordinatorAgent] Агент {self.jid} запущен.")

        # CyclicBehaviour для обработки request-сообщений от студента
        # MessageTemplate фильтрует: только performative='request' попадёт в этот обработчик
        request_template = Template(metadata={"performative": "request"})
        self.add_behaviour(CoordinatorRequestHandler(), template=request_template)

        # CyclicBehaviour для обработки inform-сообщений от руководителя
        # MessageTemplate фильтрует: только performative='inform' попадёт сюда
        inform_template = Template(metadata={"performative": "inform"})
        self.add_behaviour(CoordinatorInformHandler(), template=inform_template)

        # PeriodicBehaviour — контроль дедлайнов каждые 8 секунд
        self.add_behaviour(DeadlineCheckerBehaviour(period=8))
