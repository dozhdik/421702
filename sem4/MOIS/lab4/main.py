"""
Точка входа многоагентной системы управления этапами курсового проекта.

Запуск: python main.py

Система создаёт 3 агента (Student, Supervisor, Coordinator),
подключает их к XMPP-серверу и запускает демонстрационный сценарий:
  1. Студент подаёт тему
  2. Координатор пересылает руководителю
  3. Руководитель рецензирует (FSM) и утверждает
  4. Координатор возвращает решение студенту
  5. Студент переходит к следующему этапу (повтор для 4 этапов)
  6. Параллельно координатор контролирует дедлайны (PeriodicBehaviour)
"""

import asyncio
import logging
import sys

from agents import StudentAgent, SupervisorAgent, CoordinatorAgent
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("coursework_mas")


async def main():
    config_dict = {
        "student_jid": Config.STUDENT_JID,
        "supervisor_jid": Config.SUPERVISOR_JID,
        "coordinator_jid": Config.COORDINATOR_JID,
    }

    logger.info("Инициализация МАС управления курсовым проектом...")
    logger.info(f"XMPP-сервер: {Config.XMPP_SERVER}:{Config.XMPP_PORT}")

    # Создание агентов
    student = StudentAgent(Config.STUDENT_JID, Config.STUDENT_PASS, config_dict)
    supervisor = SupervisorAgent(Config.SUPERVISOR_JID, Config.SUPERVISOR_PASS, config_dict)
    coordinator = CoordinatorAgent(Config.COORDINATOR_JID, Config.COORDINATOR_PASS, config_dict)

    agents = [coordinator, supervisor, student]

    # Запуск агентов с обработкой ошибок подключения
    for agent in agents:
        try:
            await agent.start(auto_register=True)
            logger.info(f"Агент {agent.jid} подключён.")
        except Exception as e:
            logger.error(f"Ошибка подключения агента {agent.jid}: {e}")
            # Останавливаем уже запущенных
            for a in agents:
                if a.is_alive():
                    await a.stop()
            sys.exit(1)

    logger.info("Все агенты подключены. Запуск сценария...")
    logger.info("=" * 60)

    # Ожидание завершения сценария (студент пройдёт все 4 этапа)
    timeout = 90
    elapsed = 0
    try:
        while elapsed < timeout:
            await asyncio.sleep(1)
            elapsed += 1
            if student.project_done:
                logger.info("=" * 60)
                logger.info("Сценарий завершён успешно. Все этапы пройдены.")
                break
        else:
            logger.warning(f"Таймаут ({timeout} сек). Сценарий не завершился полностью.")
    except KeyboardInterrupt:
        logger.info("Прервано пользователем (Ctrl+C).")

    # Корректная остановка всех агентов
    logger.info("Остановка агентов...")
    for agent in agents:
        if agent.is_alive():
            await agent.stop()

    logger.info("Система остановлена.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
