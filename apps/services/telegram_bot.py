import logging
from collections import defaultdict
from typing import Optional

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from django.conf import settings

from apps.models import Order

logger = logging.getLogger(__name__)


class TelegramBotService:
    """Сервис для работы с Telegram Bot API через Aiogram"""

    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    async def send_order_offer(self, chat_id: str, order: Order, booking_id: str) -> bool:
        """
        Отправить офер переводчику через Aiogram

        Args:
            chat_id: Telegram chat ID переводчика
            order: Объект Order
            booking_id: ID бронирования

        Returns:
            bool - успешность отправки
        """
        # Формирование сообщения
        message = self._format_order_message(order)

        # Inline кнопки через Aiogram
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='✅ Принять заказ',
                        callback_data=f'accept_order:{booking_id}'
                    ),
                    InlineKeyboardButton(
                        text='❌ Отклонить',
                        callback_data=f'decline_order:{booking_id}'
                    )
                ]
            ]
        )

        # Отправка через Aiogram
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            logger.info(f"Sent offer to chat_id {chat_id} for order {order.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send offer to {chat_id}: {e}")
            return False

    def _format_order_message(self, order: Order) -> str:
        """Форматировать сообщение с деталями заказа"""
        slots_text = self._format_time_slots(order.selected_slots)
        languages_text = self._format_languages(order.languages.all())
        translation_types_text = self._format_translation_types(order.translation_types.all())

        # Получить даты начала и конца
        start_date = order.start_datetime.strftime('%d.%m.%Y') if order.start_datetime else 'Не указано'
        end_date = order.end_datetime.strftime('%d.%m.%Y') if order.end_datetime else 'Не указано'

        # Локация
        if order.location_type == Order.LocationType.ONLINE:
            location = 'Online'
        else:
            location = f"{order.city.name if order.city else 'Не указано'}"
            if order.address:
                location += f", {order.address}"

        message = f"""
🔔 <b>Новый заказ!</b>

📋 <b>Детали:</b>
• Тип: {translation_types_text}
• Языки: {languages_text}
• Дата начала: {start_date}
• Дата окончания: {end_date}
• Время: {slots_text}
• Локация: {location}

👤 Клиент: {order.client.get_full_name()}

⏰ У вас есть 3 часа для принятия заказа
"""
        return message

    def _format_time_slots(self, slots: Optional[list]) -> str:
        """Форматировать временные слоты"""
        if not slots:
            return "Не указано"

        # Группировать по датам
        by_date = defaultdict(list)

        for slot in slots:
            try:
                date, period = slot.rsplit('-', 1)
                period_text = 'Утро (09:00-14:00)' if period == 'morning' else 'Вечер (14:00-18:00)'
                by_date[date].append(period_text)
            except Exception as e:
                logger.error(f"Error parsing slot {slot}: {e}")
                continue

        result = []
        for date, periods in sorted(by_date.items()):
            result.append(f"{date}: {', '.join(periods)}")

        return '\n  '.join(result) if result else "Не указано"

    def _format_languages(self, languages) -> str:
        """Форматировать языки"""
        if not languages:
            return "Не указано"

        return ', '.join([lang.name for lang in languages])

    def _format_translation_types(self, translation_types) -> str:
        """Форматировать типы перевода"""
        if not translation_types:
            return "Не указано"

        return ', '.join([tt.name for tt in translation_types])

    async def send_simple_message(self, chat_id: str, text: str) -> bool:
        """
        Отправить простое текстовое сообщение

        Args:
            chat_id: Telegram chat ID
            text: Текст сообщения

        Returns:
            bool - успешность отправки
        """
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='HTML'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
            return False

    async def close(self):
        """Закрыть сессию бота"""
        await self.bot.session.close()
