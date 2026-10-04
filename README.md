# yaddd-example

Пример FastAPI-приложения, построенного по принципам **Domain-Driven Design** с использованием библиотеки [yaddd](https://github.com/netstuff/yaddd).

## Структура

```
src/
├── web.py                 # точка входа FastAPI, lifespan, exception handlers
├── composition_root.py    # composition root: связывает все слои приложения
├── config/                # настройки приложения (pydantic-settings)
│   ├── __init__.py        # агрегирующий класс Settings
│   ├── base.py            # общие настройки приложения
│   ├── db.py              # настройки БД
│   └── security.py        # настройки безопасности
├── domain/                # доменный слой
│   └── order.py           # агрегат Order, событие OrderPlaced, инварианты
├── application/           # слой приложения
│   ├── commands.py        # команды и запросы (CQS)
│   ├── dto.py             # DTO
│   ├── handlers/          # обработчики команд/запросов (auto-discovery)
│   │   ├── place_order.py
│   │   └── get_order.py
│   └── uow.py             # порт Unit of Work для заказов
├── infrastructure/        # инфраструктурный слой
│   ├── bus.py             # in-process Command/Query bus
│   ├── database.py        # таблицы, engine и фабрика сессий SQLAlchemy
│   ├── registry.py        # auto-discovery обработчиков
│   ├── repositories.py    # SQLAlchemy-реализация репозитория Order
│   └── uow.py             # SQLAlchemy Unit of Work
└── api/                   # presentation / FastAPI-адаптер
    ├── routes.py          # роуты
    └── schemas.py         # Pydantic-схемы
```

## Зависимости

Управление зависимостями через [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

## Конфигурация

Настройки живут в пакете `src/config` и описаны через `pydantic-settings` (`BaseSettings`). Каждая группа параметров — в отдельном модуле:

- `APP_NAME`, `APP_DEBUG` — `src/config/base.py`
- `DATABASE_URL` — `src/config/db.py`
- `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES` — `src/config/security.py`

По умолчанию приложение подключается к `postgresql+asyncpg://postgres:pass@localhost:5432/yaddd_example`. Переменные окружения читаются автоматически при создании `Settings()`.

## Регистрация обработчиков

Обработчики команд и запросов живут в `src/application/handlers/` и обнаруживаются автоматически (`src/infrastructure/registry.py`) по маркерам `_command` / `_query` на классах.

Чтобы добавить новый use case, достаточно положить новый модуль в `src/application/handlers/` с классом, помеченным `_command` или `_query`. `CompositionRoot` не требует изменений.

## База данных

Приложение использует PostgreSQL. URL подключения берётся из `DATABASE_URL` (см. `src/config/db.py`).

Таблицы создаются автоматически в `lifespan` при старте приложения.

## Запуск

Код приложения живёт в `src/`, который выступает как корень пакета. Uvicorn запускается с `--app-dir src`:

```bash
uv run uvicorn web:app --app-dir src --reload
```

API будет доступно по адресу http://127.0.0.1:8000.

## Настройка редактора

Так как корень пакета — `src/`, редактору нужно знать, где искать модули:

- **Pyright / Pylance (VS Code):** настройки уже в `pyproject.toml` (`[tool.pyright] extraPaths = ["src"]`) и в `.vscode/settings.json` (`python.analysis.extraPaths`). Перезапустите языковой сервер / окно редактора.
- **mypy:** использует `mypy_path = ["src"]` из `pyproject.toml`.
- **pytest:** добавляет `src` в `pythonpath` через `pyproject.toml`.

## Примеры запросов

```bash
# создать заказ
curl -X POST http://127.0.0.1:8000/orders -H 'Content-Type: application/json' -d '{"total": 100}'

# получить заказ
curl http://127.0.0.1:8000/orders/<order_id>

# ошибка доменного инварианта (422)
curl -X POST http://127.0.0.1:8000/orders -H 'Content-Type: application/json' -d '{"total": -10}'
```

## Тесты и статический анализ

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pyright src
uv run pytest tests -v
```

## Примечание по типизации

`yaddd` использует `@dataclass_transform` в `__init_subclass__` для автоматического превращения наследников `Entity`, `AggregateRoot`, `DomainEvent`, `Command`, `Query` и `DTO` в dataclass'ы. Текущие версии `mypy` и `pyright` не выводят сгенерированный `__init__` при таком расположении декоратора, поэтому в каркасе явно добавлены:

- `@dataclass(eq=False, kw_only=True)` для `Order`;
- явные `__init__` у `OrderPlaced`, `PlaceOrder`, `GetOrder`, `OrderDTO`.

Это позволяет проходить `mypy --strict` без потери runtime-поведения yaddd.
