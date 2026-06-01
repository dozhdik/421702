# Лабораторная работа №4 — Многоагентное управление этапами выполнения курсового проекта

## Вариант 21

Многоагентная система (МАС) на базе фреймворка SPADE 3.x, моделирующая управление
этапами курсового проекта с использованием протокола XMPP для межагентного общения.

---

## Дерево проекта

```
lab4/
├── main.py              # Точка входа — запуск системы
├── agents.py            # Определение агентов (Student, Supervisor, Coordinator)
├── behaviours.py        # Поведения агентов (OneShotBehaviour, CyclicBehaviour, PeriodicBehaviour, FSMBehaviour)
├── config.py            # Загрузка конфигурации из .env
├── .env                 # Конфигурация (JID, пароли, сервер) — НЕ коммитить в git
├── .env.example         # Пример конфигурации
├── requirements.txt     # Зависимости Python
└── README.md            # Документация (этот файл)
```

---

## Установка и запуск

### 1. Установка зависимостей

```bash
cd lab4
python -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### 2. Настройка XMPP-сервера

#### Вариант A: Локальный сервер Prosody (рекомендуется)

```bash
# Ubuntu/Debian
sudo apt install prosody

# Настройка /etc/prosody/prosody.cfg.lua:
# - Добавить VirtualHost "localhost"
# - Включить модули: roster, saslauth, tls, register
# - Установить allow_registration = true

sudo systemctl restart prosody

# Регистрация пользователей (или использовать auto_register=True в SPADE):
sudo prosodyctl register student localhost student123
sudo prosodyctl register supervisor localhost supervisor123
sudo prosodyctl register coordinator localhost coordinator123
```

#### Вариант B: Docker (Prosody)

```bash
docker run -d --name prosody \
  -p 5222:5222 -p 5269:5269 \
  -e DOMAIN=localhost \
  -e ALLOW_REGISTRATION=true \
  prosody/prosody
```

#### Вариант C: Публичный тестовый сервер

Измените `.env`:
```
XMPP_SERVER=jabber.hot-chilli.net
STUDENT_JID=student_test_lab4@jabber.hot-chilli.net
STUDENT_PASS=securepass1
SUPERVISOR_JID=supervisor_test_lab4@jabber.hot-chilli.net
SUPERVISOR_PASS=securepass2
COORDINATOR_JID=coordinator_test_lab4@jabber.hot-chilli.net
COORDINATOR_PASS=securepass3
```

> На публичных серверах нужно предварительно зарегистрировать аккаунты
> (через веб-интерфейс или XMPP-клиент типа Gajim/Pidgin).

### 3. Конфигурация

```bash
cp .env.example .env
# Отредактируйте .env при необходимости
```

### 4. Запуск системы

```bash
python main.py
```

---

## Демонстрационный сценарий

При запуске система автоматически выполняет следующий сценарий:

1. **Подача темы** (этап 1): StudentAgent отправляет заявку на тему координатору
2. **Маршрутизация**: CoordinatorAgent пересылает заявку руководителю
3. **Рецензирование** (FSM): SupervisorAgent проходит состояния WAIT → REVIEW → APPROVE
4. **Уведомление**: CoordinatorAgent пересылает решение студенту
5. **Следующий этап**: StudentAgent получает одобрение и отправляет отчёт по этапу 2
6. **Повтор** для этапов 2, 3, 4 (план → основная часть → финальная версия)
7. **Контроль дедлайнов**: параллельно CoordinatorAgent периодически напоминает о сроках
8. **Завершение**: после прохождения всех 4 этапов система останавливается

### Ожидаемый вывод (фрагмент):

```
12:00:01 [INFO] coursework_mas: Инициализация МАС управления курсовым проектом...
12:00:02 [INFO] coursework_mas: [StudentAgent] Агент student@localhost запущен.
12:00:02 [INFO] coursework_mas: [SupervisorAgent] Агент supervisor@localhost запущен.
12:00:02 [INFO] coursework_mas: [CoordinatorAgent] Агент coordinator@localhost запущен.
12:00:05 [INFO] coursework_mas: [Student] Заявка на тему отправлена координатору.
12:00:05 [INFO] coursework_mas: [Coordinator] Получен запрос от student@localhost: ЭТАП 1...
12:00:05 [INFO] coursework_mas: [Coordinator] Материалы переданы руководителю на рецензию.
12:00:05 [INFO] coursework_mas: [Supervisor/FSM] Получены материалы на проверку...
12:00:07 [INFO] coursework_mas: [Supervisor/FSM] Решение: УТВЕРЖДЕНО.
12:00:07 [INFO] coursework_mas: [Coordinator] Решение передано студенту.
12:00:07 [INFO] coursework_mas: [Student] Этап 1 принят. Переход к этапу 2.
...
12:00:30 [INFO] coursework_mas: [Student] ВСЕ ЭТАПЫ ПРОЙДЕНЫ. Курсовой проект защищён!
12:00:31 [INFO] coursework_mas: Сценарий завершён успешно.
```

---

## Чек-лист соответствия требованиям лабораторной работы

| # | Требование | Реализация | Статус |
|---|-----------|-----------|--------|
| 1 | Python 3.9+, SPADE 3.x, XMPP | `spade>=3.3.0`, протокол XMPP, Python 3.9+ | ✅ |
| 2 | Не менее 3 агентов | StudentAgent, SupervisorAgent, CoordinatorAgent | ✅ |
| 3 | Минимум 2 типа поведений | OneShotBehaviour, CyclicBehaviour, PeriodicBehaviour, FSMBehaviour (4 типа) | ✅ |
| 4 | FIPA-метаданные + MessageTemplate | `msg.set_metadata("performative", ...)`, `Template(metadata={...})` при `add_behaviour()` | ✅ |
| 5 | Сценарий управления этапами | Подача темы → согласование → контроль дедлайнов → этапы 1-4 → защита | ✅ |
| 6 | Обработка ошибок, логирование, комментарии | `try/except` при подключении, `logging` модуль, docstring-комментарии | ✅ |

---

## Архитектура взаимодействия

```
┌─────────────┐     request      ┌──────────────────┐     request      ┌─────────────────┐
│ StudentAgent│ ───────────────► │ CoordinatorAgent │ ───────────────► │ SupervisorAgent │
│             │                  │                  │                  │   (FSMBehaviour) │
│ OneShotBeh. │ ◄─────────────── │  CyclicBeh. x2   │ ◄─────────────── │                 │
│ CyclicBeh.  │     inform       │  PeriodicBeh.    │     inform       │ WAIT→REVIEW→    │
└─────────────┘                  └──────────────────┘                  │ APPROVE/REJECT  │
                                        │                              └─────────────────┘
                                        │ inform (deadline)
                                        ▼
                                 ┌─────────────┐
                                 │ StudentAgent│
                                 └─────────────┘
```

---

## Используемые FIPA-метаданные

| Поле | Значения | Назначение |
|------|---------|-----------|
| `performative` | `request`, `inform` | Тип речевого акта (запрос / информирование) |
| `protocol` | `coursework-management` | Идентификатор протокола взаимодействия |
| `ontology` | `topic-submission`, `stage-report`, `review-approved`, `deadline-reminder`, ... | Семантика содержимого |
| `language` | `Russian` | Язык содержимого |

---

## Технические детали

- **FSMBehaviour** (SupervisorAgent): состояния `STATE_WAIT` → `STATE_REVIEW` → `STATE_APPROVE`/`STATE_REJECT` → `STATE_WAIT`. Переходы регистрируются через `fsm.add_transition(source, dest)`.
- **MessageTemplate**: при `self.add_behaviour(behaviour, template=...)` SPADE направляет в поведение только сообщения, соответствующие шаблону. Это позволяет разделить обработку `request` и `inform` в разных поведениях одного агента.
- **PeriodicBehaviour**: `DeadlineCheckerBehaviour(period=8)` — каждые 8 секунд проверяет дедлайны и отправляет напоминания.
- **auto_register=True**: при запуске агенты автоматически регистрируются на XMPP-сервере (если сервер поддерживает In-Band Registration).
