<p align="center">  
<strong>Асинхронный Python SDK для работы с Playerok API</strong><br>  
GraphQL • Streaming • Proxy • Production-ready transport  
</p>
  
<p align="center">  
<a href="https://pypi.org/project/PyPlayerokAPI/">  
<img src="https://img.shields.io/pypi/v/PyPlayerokAPI.svg" alt="PyPI version">  
</a>  
<a href="https://pypi.org/project/PyPlayerokAPI/">  
<img src="https://img.shields.io/pypi/pyversions/PyPlayerokAPI.svg" alt="Python Version">  
</a>  
<a href="https://github.com/your-repo/PyPlayerokAPI/blob/main/LICENSE">  
<img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">  
</a>  
<img src="https://img.shields.io/badge/async-ready-blue.svg" alt="Async Ready">  
</p>
<p align="center">
<a href="https://github.com/kekch127/PyPlayerokAPI/stargazers">
<img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fkekch127%2FPyPlayerokAPI&query=%24.stargazers_count&style=for-the-badge&label=stars&color=43d433&logo=github" alt="stars">
</a>
<a href="https://github.com/kekch127/PyPlayerokAPI/forks">
<img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fkekch127%2FPyPlayerokAPI&query=%24.forks_count&style=for-the-badge&label=forks&color=%236c70e6&logo=github" alt="forks">
</a>
<a href="https://t.me/TheKekich">
<img src="https://img.shields.io/badge/telegram-%D1%80%D0%B0%D0%B7%D1%80%D0%B0%D0%B1%D0%B0-green?style=for-the-badge&logo=telegram" alt="telegram">
</a>
</p>

---
**PyPlayerokAPI** — неофициальная Python-библиотека для взаимодействия с торговой площадкой Playerok через GraphQL API и систему потоковых событий. 
  
Что можно сделать с помощью библиотеки:  
  
- 🤖 автоматизацию  
- 📊 мониторинг сделок  
- 💬 работы с чатами  
- 💰 управления транзакциями  
- 🔄 обработки событий в реальном времени  
- 🧩 интеграции в собственные сервисы  

---
# 📚 Содержание

- [Особенности](#Особенности)
- [Требования](#Требования)
- [Установка](#Установка)
- [Аутентификация](#Аутентификация)
- [Структура библиотеки](#Структура-библиотеки)
- [Примеры использования](#Примеры-использования)
	- [Предисловие](#Предисловие)
	- [Общие варианты использования](#Общие-варианты-использования)
	- [Готовые варианты использования](#Готовые-варианты-использования)
- [Тесты](#Тесты)
- [Дополнительная информация](#Дополнительная-информация)
- [Текущий changelog](docs/changelogs/latest.md)
- [Проверить историю changelog-ов](docs/changelogs/history.md)

---
# Особенности

- Выполнение запросов GraphQL
- Поддержка Persisted queries 
- Модуль управления аккаунтом
- Стриминг & обработка событий в реальном времени
- Поддержка прокси
- Аутентификация на основе токена
- Кастомный транспортный уровень, совместимый с Cloudflare (через `tls_requests` и `curl_cffi`)

---
# Требования

- Python 3.11+
- token аккаунта Playerok
- Прокси (HTTP/S) (опционально)

---
# Установка

### Через PyPI
```bash
pip install PyPlayerokAPI
```

### С помощью pip
```bash
pip install git+https://github.com/kekch127/PyPlayerokAPI.git
```

### Из репозитория
```bash
git clone https://github.com/kekch127/PyPlayerokAPI.git
cd PyPlayerokAPI
pip install -e .
```

---
# Аутентификация

Для использования необходимо сначала получить токен аккаунта Playerok. Для этого авторизуйтесь на сайте, после с помощью любого расширения (я использую EditThisCookie V3) получите JWT токен из Cookie файлов. Токен находится по следующему пути:

```
.playerok.com | token
```

---
# Структура библиотеки

```
PyPlayerokAPI/
│
├── account/
│   ├── Содержит все миксины для управления аккаунтом
│
├── models/
│   ├── Содержит все модели, описывающие аккаунт, сделки и т.д. (Pydantic)
│
├── stream/
|   ├── events/
|   |   ├── Содержит реализацию обработки всех типов ивентов
|   |   ├── markers/
|   |   |   ├── Содержит реализацию создания маркеров
|   |
|   ├── listener/
|   |   ├── Содержит реализацию листенера и клиента websocket
|
├── types/
|   ├── Содержит константы
|
├── cacert.pem 
├── graphql.py Билдер payload запросов для GraphQL
├── transport.py Транспортный слой
```

---
# Примеры использования

## Предисловие

### Стримы

`PlayerokAccountListener` и `PlayerokMultiAccountListener` запускают фоновых воркеров:
- WebSocket стрим (`chatUpdated`, `chatMessageCreated`, `userUpdated`)
- Deal стрим (ищет только новые созданные чаты с ивентом `{{ITEM_PAID}}`)
- Review стрим (проверяет сделки которые ожидают новый отзыв)

### Ивенты

Все события описываются в одной модели - `PlayerokEvent`.
В мульти аккаунт моде обработчики получают:
- `account: AccountClient`
- `event: PlayerokEvent`

или одну обертку:
- `account_event: AccountEvent`

### Рекомендуемые сигнатуры хендлеров

```python
async def handler(account: AccountClient, event: PlayerokEvent) -> None:
    ...
```

```python
async def handler(account_event: AccountEvent) -> None:
    ...
```

### Поддержка ивентов

Поддерживаются все типы `EventTypes`:
- `CHAT_INITIALIZED` - Чат инициализирован
- `NEW_MESSAGE` - Новое сообщение в чате
- `NEW_DEAL` - Создана новая сделка (когда покупатель оплатил товар)
- `NEW_REVIEW` - Новый отзыв от покупателя
- `DEAL_CONFIRMED` - Сделка подтверждена (покупатель подтвердил получение предмета)
- `DEAL_CONFIRMED_AUTOMATICALLY` - Сделка подтверждена автоматически (если покупатель долго не выходит на связь)
- `DEAL_ROLLED_BACK` - Продавец оформил возврат сделки
- `DEAL_HAS_PROBLEM` - Пользователь сообщил о проблеме в сделке
- `DEAL_PROBLEM_RESOLVED` - Проблема в сделке решена
- `DEAL_STATUS_CHANGED` - Статус сделки изменён
- `ITEM_PAID` - Пользователь оплатил предмет
- `ITEM_SENT` - Предмет отправлен (продавец подтвердил выполнение сделки)

Маппинг маркеров:
- `{{ITEM_PAID}}` -> `NEW_DEAL`, `ITEM_PAID`
- `{{ITEM_SENT}}` -> `ITEM_SENT`, `DEAL_STATUS_CHANGED`
- `{{DEAL_CONFIRMED}}` -> `DEAL_CONFIRMED`, `DEAL_STATUS_CHANGED`
- `{{DEAL_CONFIRMED_AUTOMATICALLY}}` -> `DEAL_CONFIRMED_AUTOMATICALLY`, `DEAL_STATUS_CHANGED`
- `{{DEAL_ROLLED_BACK}}` -> `DEAL_ROLLED_BACK`, `DEAL_STATUS_CHANGED`
- `{{DEAL_HAS_PROBLEM}}` -> `DEAL_HAS_PROBLEM`, `DEAL_STATUS_CHANGED`
- `{{DEAL_PROBLEM_RESOLVED}}` -> `DEAL_PROBLEM_RESOLVED`, `DEAL_STATUS_CHANGED`

### Важные правила

1. Вызывать `listener.start()` только внутри запущенного `loop`. 
2. Использовать полный JWT токен аккаунта.
3. Не использовать `while True: asyncio.run(...)`.
4. Если используете декораторы, сохраняйте `dispatch = True` (дефолт).
5. Если хотите использовать очередь вручную, установите `dispatch = False`.

#### Так-же не забывайте, что
Используйте `await asyncio.Event().wait() ` как `бесконечный блокер` когда:
1. Это простой standalone-скрипт
2. Все нужные воркеры уже запущены в фоне
3. Больше нет ни одного await, который держит loop живым

В ином другом случае, когда уже есть естественная точка блокировки - не используем. Пример:
- (aiogram) `await dp.start_polling(bot)`
- (ручное чтение очереди) `while True: item = await listener.get()`
-  `await server.serve_forever()`
- и т.д.

---
## Общие варианты использования

### Стандартная инициализация аккаунта
```python
from PyPlayerokAPI.account import AccountClient

account = AccountClient(
	token = "JWT_TOKEN_HERE", # обязательное поле
	user_agent = "", # необязательное поле (но желательное) (для разных аккаунтов используйте ранзые юзер агенты для избежания блокировки)
	proxy = "" # необязательное поле (но желательное)
)

print(account.account_data) # получаем информацию об аккаунте
```

### Поиск сообщений
Вы можете настроить хендлер нового сообщения на поиск определенного:
- текста
- regex
- наличию одному или множесту ключевым словам в тексте
- наличию всех ключевых слов

```python
async def main():
    clients = [
        AccountClient(
            token = item["token"], user_agent = item["user_agent"]
        )
        for item in ACCOUNTS
    ]
    
    listener = PlayerokMultiAccountListener(clients)
    router = listener._router
    
    for acc in listener.listeners:
		# Выставляем хендл по определенному тексту
        acc._factory.track_text("g", "в профиле Playerok")

		# Выставляем хендл по определенному regex
        acc._factory.track_regex("gg", r"\d")

		# Выставляем хендл по ОДНОМУ из ключевых слов 
		# (Обработчик срабоатает, если в сообщении есть одно из заданных слов)
        acc._factory.track_contains_any("ggg", ["Playerok", "Ботом", "больше"])

		# Выставляем хендл по ВСЕМ ключевым словам
		# (Обработчик сработает, если в сообщении есть ВСЕ из заданных слов)
        acc._factory.track_contains_all("gggg", ["Изменить", "аватар"])
    
    
	# Поиск по определенному тексту в сообщении
    @router.on_new_message(marker = "g")
    async def handle(account, event: PlayerokEvent):
        print(f"НАЙДЕН ТЕКСТ: {event.message.text}")
    
	# Поиск по regex
    @router.on_new_message(marker = "gg")
    async def handle1(account, event: PlayerokEvent):
        print(f"НАЙДЕН regex: {event.message.text}")
    
	# Поиск по наличию ОДНОГО из ключевых слов
    @router.on_new_message(marker = "ggg")
    async def handle2(account, event: PlayerokEvent):
        print(f"НАЙДЕНО КЛЮЧЕВОЕ СЛОВО ИЗ СПИСКА: {event.message.text}")
    
	# Поиск по наличию ВСЕХ ключевых слов
    @router.on_new_message(marker = "gggg")
    async def handle3(account, event: PlayerokEvent):
        print(f"НАЙДЕНЫ ВСЕ КЛЮЧЕВЫЕ СЛОВА: {event.message.text}")
    
	# обычный роутер на любое сообщение
    @router.on_new_message()
    async def on_new_message(account: AccountClient, event: PlayerokEvent):
        print(f"[MSG] for account {account.account_data.username}: {event.message.text}")


    await listener.start()
    await asyncio.Event().wait()
```


### Выставление предмета на продажу
```python
from PyPlayerokAPI.account import AccountClient

account = AccountClient(token = "", user_agent = "")

# получаем информацию игры
game = account.get_game(slug = "minecraft")

# # получаем необходимую категорию (все доступные категории описаны в game.categories)
game_category = account.get_game_category(
    id = [category for category in game.categories if category.name == "Ключи"][0].id
)

# получаем варианты "доставки" товара в этой категории
game_obtaining_type_list = account.get_game_category_obtaining_types(
    game_category_id = game_category.id
)

# выбираем тип выдачи "Без входа в аккаунт"
choosed_obtaining_type = [
    obt_type for obt_type in game_obtaining_type_list.obtaining_types if obt_type.name == "Без входа в аккаунт"
][0]

# выбираем вариант версии игры (pc, mobile, ps, xbox)
gift_type_option = [
    gift_type for gift_type in game_category.options if gift_type.value == "pc"
]

# получаем поля с данными категории определенного типа выдачи
data_fields_list = account.get_game_category_data_fields(
    game_category_id = game_category.id,
    obtaining_type_id = choosed_obtaining_type.id
)

# Берем поле с данными о комментарии (все доступные поля описаны в data_fields_list.data_fields)
comment_data_field = [
    data_field for data_field in data_fields_list.data_fields if data_field.label == "Комментарий"
][0]

# Задаем значение данному полю, так как оно обязательное (не менее 10 симовлов)
comment_data_field.value = "Спасибо! Заказывайте у нас еще!"

# Берем поле с данными о ключе
key_data_field = [
    data_field for data_field in data_fields_list.data_fields if data_field.label == "Ключ"
][0]

# Задаем значение данному полю, так как оно обязательное
key_data_field.value = "J73D2-XXXXX-XXXXX-XXXXX-XXXXX"

# описываем путь к файлу фотографии для карточки товара
banner_attachment = "banner.jpg"

# вызываем метод создания товара
item = account.create_item(
    game_category_id = game_category.id, # указываем id категории игры
    obtaining_type_id = choosed_obtaining_type.id, # указывает id типа получения товара
    name = "Ключ MINECRAFT JAVA / BEDROCK", # указываем название товара
    price = 1700, # указываем цену товара
    description = """
🌹Активация через Веб-браузер:
1️⃣ Запустите веб-браузер и перейдите по адресу: https://redeem.microsoft.com
2️⃣ Войдите, используя свои учетные данные Microsoft
3️⃣Введите код активации и нажмите «Далее»; следуйте инструкциям для подтверждения
    """, # указываем описание товара
    options = gift_type_option, # указываем вариант товара
    data_fields = [comment_data_field, key_data_field], # указываем поля с данными предмета
    attachments = [banner_attachment] # указываем фотографии и тд
)

# Публикуем предмет
statuses = account.get_item_priority_statuses(
    item_id = item.id,
    item_price = str(item.price)
)

new_item = account.publish_item(
    item_id = item.id,
    priority_status_id = f"{next(status.id for status in statuses if status.price == 0 or status.name == "Обычный")}" # выставляем приоритет
)
```

---
## Готовые варианты использования
### Быстрый старт и простой одиночный клиент

```python
import asyncio

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.stream import PlayerokAccountListener
from PyPlayerokAPI.stream.events import AccountEvent, PlayerokEvent

TOKEN = ""
USER_AGENT = ""

async def main():
	account = AccountClient(token = TOKEN, user_agent = USER_AGENT)
	listener = PlayerokAccountListener(account)
	router = listener.router
	
	@router.on_new_message()
	async def on_new_message(account: AccountClient, event: PlayerokEvent) -> None:
		print(f"[MSG] for account {account.account_data.username}: {event.message.text}")
	
	listener.start()
	await asyncio.Event().wait() 

if __name__ == "__main__":
	asyncio.run(main())
```

### Множество клиентов
```python
import asyncio

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.stream import PlayerokMultiAccountListener
from PyPlayerokAPI.stream.events import PlayerokEvent


ACCOUNTS = [
    {
        "token": "",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",

    },
    {
        "token": "",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    },
]

  
async def main():
    clients = [
        AccountClient(token = item["token"], user_agent = item["user_agent"])
        for item in ACCOUNTS
    ]

    listener = PlayerokMultiAccountListener(clients)
    router = listener._router

    @router.on_new_message()
    async def on_new_message(account: AccountClient, event: PlayerokEvent):
        text = event.message.text if event.message else None
        print(f"[MSG] for account {account.account_data.username}: {event.message.text}")

    @router.on_item_paid()
    async def on_item_paid(account: AccountClient, event: PlayerokEvent):
        print(f"[ITEM_PAID] for account {account.account_data.username}: {event.deal.id}")

    listener.start()
    await asyncio.Event().wait()

  
if __name__ == "__main__":
    asyncio.run(main())
```

### Мануал мод (чтение ивентов напрямую в обход диспатчера)
```python
import asyncio

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.stream import PlayerokMultiAccountListener
from PyPlayerokAPI.stream.events import AccountEvent

  
ACCOUNTS = [
    {
        "token": "",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    },
]

  
async def main():
    clients = [
        AccountClient(token = item["token"], user_agent = item["user_agent"])
        for item in ACCOUNTS
    ]

    listener = PlayerokMultiAccountListener(clients)

    # dispatch = False: без декораторов, ручной перебор очереди
    listener.start(dispatch = False)

    while True:
        item: AccountEvent = await listener.get()
        event = item.event
        print(
            "EVENT",
            item.account.token[:10],
            event.type.name,
            event.chat.id if event.chat else None,
        )
        print(f"[EVENT] for account {item.account.account_data.username}:{event.type.name} - {event.chat.id}")
        
        # ИЛИ
        
        async for event in listener:
	        print(f"[EVENT] for account {event.account.account_data.username}:{event.type.name} - {event.chat.id}")

  
if __name__ == "__main__":
    asyncio.run(main())
```

### Использование всех декораторов
```python
import asyncio

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.stream import PlayerokMultiAccountListener
from PyPlayerokAPI.stream.events import PlayerokEvent

  
ACCOUNTS = [
    {
        "token": "",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    },
]

  
def handle(event_name: str, account: AccountClient, event: PlayerokEvent):
    chat_id = event.chat.id if event.chat else None
    msg = event.message.text if event.message else None
    deal_id = event.deal.id if event.deal else None
    print(event_name, account.token[:10], chat_id, msg, deal_id)

  
async def main():
    clients = [
        AccountClient(token = item["token"], user_agent = item["user_agent"])
        for item in ACCOUNTS
    ]
    
    listener = PlayerokMultiAccountListener(clients)
    router = listener._router

  
    @router.on_chat_initialized()
    async def on_chat_initialized(account: AccountClient, event: PlayerokEvent):
        handle("CHAT_INITIALIZED", account, event)

    @router.on_new_message()
    async def on_new_message(account: AccountClient, event: PlayerokEvent):
        handle("NEW_MESSAGE", account, event)

    @router.on_new_deal()
    async def on_new_deal(account: AccountClient, event: PlayerokEvent):
        handle("NEW_DEAL", account, event)

    @router.on_new_review()
    async def on_new_review(account: AccountClient, event: PlayerokEvent):
        handle("NEW_REVIEW", account, event)

    @router.on_deal_confirmed()
    async def on_deal_confirmed(account: AccountClient, event: PlayerokEvent):
        handle("DEAL_CONFIRMED", account, event)

    @router.on_deal_confirmed_automatically()
    async def on_deal_confirmed_auto(account: AccountClient, event: PlayerokEvent):
        handle("DEAL_CONFIRMED_AUTOMATICALLY", account, event)

    @router.on_deal_rolled_back()
    async def on_deal_rolled_back(account: AccountClient, event: PlayerokEvent):
        handle("DEAL_ROLLED_BACK", account, event)

    @router.on_deal_has_problem()
    async def on_deal_has_problem(account: AccountClient, event: PlayerokEvent):
        handle("DEAL_HAS_PROBLEM", account, event)

    @router.on_deal_problem_resolved()
    async def on_deal_problem_resolved(account: AccountClient, event: PlayerokEvent):
        handle("DEAL_PROBLEM_RESOLVED", account, event)

    @router.on_deal_status_changed()
    async def on_deal_status_changed(account: AccountClient, event: PlayerokEvent):
        handle("DEAL_STATUS_CHANGED", account, event)

    @router.on_item_paid()
    async def on_item_paid(account: AccountClient, event: PlayerokEvent):
        handle("ITEM_PAID", account, event)

    @router.on_item_sent()
    async def on_item_sent(account: AccountClient, event: PlayerokEvent):
        handle("ITEM_SENT", account, event)

    listener.start()
    await asyncio.Event().wait()

  
if __name__ == "__main__":
    asyncio.run(main())
```

### Использование в боте на основе aiogram
```python
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.stream import PlayerokMultiAccountListener
from PyPlayerokAPI.stream.events import PlayerokEvent

  
BOT_TOKEN = "PUT_TELEGRAM_BOT_TOKEN_HERE"
ADMIN_CHAT_ID = 123456789

ACCOUNTS = [
    {
        "token": "",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    },
    {
        "token": "",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    },
]

  
def build_clients() -> list[AccountClient]:
    return [
        AccountClient(token = item["token"], user_agent = item["user_agent"])
        for item in ACCOUNTS
    ]
  
  
def install_stream_handlers(listener: PlayerokMultiAccountListener, bot: Bot):
    router = listener._router

    @router.on_new_message()
    async def on_new_message(account: AccountClient, event: PlayerokEvent):
        text = event.message.text if event.message and event.message.text else "<empty>"
        chat_id = event.chat.id if event.chat else "unknown"
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"[{account.token[:10]}] NEW_MESSAGE chat={chat_id}\n{text}",
        )

    @router.on_item_paid()
    async def on_item_paid(account: AccountClient, event: PlayerokEvent):
        deal_id = event.deal.id if event.deal else "unknown"
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"[{account.token[:10]}] ITEM_PAID deal={deal_id}",
        )

  
async def main():
    bot = Bot(token = BOT_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("ping"))
    async def ping(message: Message):
        await message.answer("pong")

    listener = PlayerokMultiAccountListener(build_clients())
    install_stream_handlers(listener, bot)
    listener.start()

    await dp.start_polling(bot)

  
if __name__ == "__main__":
    asyncio.run(main())
```

---
# Тесты

Библиотека предусматривает встроенные тесты, дабы вы проверили ее функциональность. 
`pytest.ini` содержит конфигурационный файл тестов. Измените его, если вы знаете, что делаете.

Для вызова тестов необходимо установить библиотеку pytest следующей командой:
```bash
pip install pytest pytest-asyncio
```

После запустите тесты
```bash
pytest -v
```

---
# Дополнительная информация

Данная библиотека является переработанной и архитектурно переосмысленной версией проекта [PlayerokAPI](https://github.com/alleexxeeyy/PlayerokAPI). 
  
Кодовая база была полностью реорганизована с упором на:  
  
- читаемость  
- масштабируемость  
- модульную архитектуру  
- соответствие современным Python-практикам  
  
Проект не является форком, а представляет собой самостоятельную реализацию с переработанной структурой.