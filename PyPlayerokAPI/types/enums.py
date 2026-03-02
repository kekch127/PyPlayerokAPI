# -*- coding=utf-8 -*-

from enum import IntEnum

# =========== EVENTS ===========
class EventTypes(IntEnum):
    CHAT_INITIALIZED = 0 # Чат инициализирован
    NEW_MESSAGE = 1 # Новое сообщение в чате
    NEW_DEAL = 2 # Создана новая сделка (когда покупатель оплатил товар)
    NEW_REVIEW = 3 # Новый отзыв от покупателя
    DEAL_CONFIRMED = 4 # Сделка подтверждена (покупатель подтвердил получение предмета)
    DEAL_CONFIRMED_AUTOMATICALLY = 5 # Сделка подтверждена автоматически (если покупатель долго не выходит на связь)
    DEAL_ROLLED_BACK = 6 # Продавец оформил возврат сделки
    DEAL_HAS_PROBLEM = 7 # Пользователь сообщил о проблеме в сделке
    DEAL_PROBLEM_RESOLVED = 8 # Проблема в сделке решена
    DEAL_STATUS_CHANGED = 9 # Статус сделки изменён
    ITEM_PAID = 10 # Пользователь оплатил предмет
    ITEM_SENT = 11 # Предмет отправлен (продавец подтвердил выполнение сделки)


class ItemLogEvents(IntEnum):
    PAID = 0 # Продавец подтвердил выполнение сделки
    SENT = 1 # Товар сделки отправлен
    DEAL_CONFIRMED = 2 # Сделка подтверждена
    DEAL_ROLLED_BACK = 3 # Сделка возвращена
    PROBLEM_REPORTED = 4 # Отправлена жалоба (создана проблема)
    PROBLEM_RESOLVED = 5 # Проблема решена 


# =========== Transaction ===========
class TransactionOperations(IntEnum):
    DEPOSIT = 0  # Пополнение
    BUY = 1  # Оплата товара
    SELL = 2  # Продажа товара
    ITEM_DEFAULT_PRIORITY = 3  # Оплата бесплатного приоритета
    ITEM_PREMIUM_PRIORITY = 4  # Оплата премиум приоритета
    WITHDRAW = 5  # Выплата
    MANUAL_BALANCE_INCREASE = 6  # Начисление на баланс аккаунта
    MANUAL_BALANCE_DECREASE = 7  # Списание с баланса аккаунта
    REFERRAL_BONUS = 8  # Приглашение друга (реферал)
    STEAM_DEPOSIT = 9  # Оплата пополнения Steam


class TransactionDirections(IntEnum):
    IN = 0  # Начисление
    OUT = 1  # Списание


class TransactionStatuses(IntEnum):
    PENDING = 0  # В ожидании
    PROCESSING = 1  # В заморозке
    CONFIRMED = 2  # Подтверждена
    ROLLED_BACK = 3  # Возврат
    FAILED = 4  # Ошибка


class TransactionPaymentMethodIds(IntEnum):
    MIR = 0  # Банковская карта МИР
    VISA_MASTERCARD = 1  # Банковская карта VISA/Mastercard
    ERIP = 2  # ЕРИП


class TransactionProviderDirections(IntEnum):
    IN = 0  # Пополнение
    OUT = 1  # Вывод


class TransactionProviderIds(IntEnum):
    LOCAL = 0  # Баланс аккаунта
    SBP = 1  # СБП
    BANK_CARD_RU = 2  # Банковская карта России
    BANK_CARD_BY = 3  # Банковская карта Беларуси
    BANK_CARD = 4  # Иностранная банковская карта
    YMONEY = 5  # ЮMoney
    USDT = 6  # USDT (TRC20)
    PENDING_INCOME = 7  # Пополнение из замороженных средств
    BANK_CARD_KZ = 8 


class BankCardTypes(IntEnum):
    MIR = 0  # МИР
    VISA = 1  # VISA
    MASTERCARD = 2  # Mastercard


# =========== ITEMS ===========
class ItemDealStatuses(IntEnum):
    PAID = 0  # Оплачена
    PENDING = 1  # Ожидает отправки
    SENT = 2  # Отправлена
    CONFIRMED = 3  # Подтверждена
    CONFIRMED_AUTOMATICALLY = 4  # Подтверждена автоматически
    ROLLED_BACK = 5  # Возвращена


class ItemDealDirections(IntEnum):
    IN = 0  # Покупка
    OUT = 1  # Продажа


class ItemStatuses(IntEnum):
    PENDING_APPROVAL = 0  # На модерации
    PENDING_MODERATION = 1  # Ожидает проверки изменений
    APPROVED = 2  # Активный
    DECLINED = 3  # Отклонён
    BLOCKED = 4  # Заблокирован
    EXPIRED = 5  # Истёк
    SOLD = 6  # Продан
    DRAFT = 7  # Черновик


# =========== CHATS ===========
class ChatTypes(IntEnum):
    PM = 0  # Приватный чат
    NOTIFICATIONS = 1  # Чат уведомлений
    SUPPORT = 2  # Чат поддержки


class ChatStatuses(IntEnum):
    NEW = 0  # Новый чат
    FINISHED = 1  # Завершённый чат


class ChatMessageButtonTypes(IntEnum):
    REDIRECT = 0  # Перенаправление по ссылке
    LOTTERY = 1  # Переход к розыгрышу
    ASK_FOR_EXTERNAL_REVIEW = 2 # Отзыв на Otzovik


# =========== REVIEW TYPES ===========
class ReviewStatuses(IntEnum):
    APPROVED = 0  # Активный
    DELETED = 1  # Удалён


# =========== GAMES TYPES ===========
class GameTypes(IntEnum):
    GAME = 0  # Игра
    APPLICATION = 1  # Приложение
    MOBILE_GAME = 2 # Мобильная игра


class GameCategoryAgreementIconTypes(IntEnum):
    # TODO: Доделать все типы иконок соглашений
    RESTRICTION = 0 # Ограничение
    CONFIRMATION = 0 # Подтверждение


class GameCategoryOptionTypes(IntEnum):
    # TODO: Доделать все типы опций категории
    SELECTOR = 0 # Выбор типа
    SWITCH = 1 # Переключатель


class GameCategoryDataFieldTypes(IntEnum):
    ITEM_DATA = 0  # Данные предмета
    OBTAINING_DATA = 1  # Получаемые данные


class GameCategoryDataFieldInputTypes(IntEnum):
    # TODO: Доделать все типы вводимых дата-полей
    INPUT = 0 # Вводимое значение (вводится покупателем при оформлении предмета)


class GameCategoryAutoConfirmPeriods(IntEnum):
    # TODO: Доделать все периоды авто-подтверждения
    SEVEN_DEYS = 0 # Семь дней


class GameCategoryInstructionTypes(IntEnum):
    FOR_SELLER = 0 # Для продавца
    FOR_BUYER = 1 # Для покупателя


# =========== OTHER TYPES ===========
class UserTypes(IntEnum):
    USER = 0  # Пользователь
    MODERATOR = 1  # Модератор
    BOT = 2  # Бот
    ADMIN = 3 # Администратор


class SortDirections(IntEnum):
    DESC = 0  # По убыванию
    ASC = 1  # По возрастанию


class PriorityTypes(IntEnum):
    DEFAULT = 0  # Стандартный
    PREMIUM = 1  # Премиум