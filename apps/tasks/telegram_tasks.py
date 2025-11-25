"""
Celery tasks для Telegram интеграции и Order Workflow
"""
import asyncio
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def send_order_offer_notification(booking_id: str):
    """
    Отправить уведомление переводчику о новом офере через Telegram

    Args:
        booking_id: ID бронирования
    """
    from apps.models import Booking
    from apps.services.telegram_bot import TelegramBotService

    try:
        booking = Booking.objects.get(id=booking_id)
        interpreter = booking.interpreter

        if not interpreter.telegram_chat_id:
            logger.warning(f"Interpreter {interpreter.id} has no telegram_chat_id")
            return {'success': False, 'error': 'No telegram_chat_id'}

        # Создать сервис и отправить сообщение
        bot_service = TelegramBotService()

        # Запустить async функцию
        success = asyncio.run(bot_service.send_order_offer(
            interpreter.telegram_chat_id,
            booking.order,
            str(booking.id)
        ))

        # Закрыть сессию
        asyncio.run(bot_service.close())

        if success:
            logger.info(f"Sent offer notification to interpreter {interpreter.id}")
            return {'success': True}
        else:
            logger.error(f"Failed to send offer to interpreter {interpreter.id}")
            return {'success': False, 'error': 'Failed to send message'}

    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_id} not found")
        return {'success': False, 'error': 'Booking not found'}
    except Exception as e:
        logger.error(f"Error sending offer notification for booking {booking_id}: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def expire_order_offers(order_id: str):
    """
    Автоматически истечь оферы через 3 часа

    Запускается с задержкой 3 часа после отправки оферов

    Args:
        order_id: ID заказа
    """
    from apps.models import Booking, Order
    from apps.services.telegram_bot import TelegramBotService

    try:
        order = Order.objects.get(id=order_id)

        # Найти все неотвеченные оферы
        pending_bookings = Booking.objects.filter(
            order=order,
            status=Booking.Status.OFFERED,
            is_expired=False
        )

        expired_count = 0
        bot_service = TelegramBotService()

        for booking in pending_bookings:
            # Проверить, истек ли срок
            if booking.offer_expires_at and timezone.now() >= booking.offer_expires_at:
                booking.is_expired = True
                booking.status = Booking.Status.EXPIRED
                booking.save()

                expired_count += 1

                # Уведомить переводчика
                if booking.interpreter.telegram_chat_id:
                    asyncio.run(bot_service.send_simple_message(
                        chat_id=booking.interpreter.telegram_chat_id,
                        text="⏰ Время для принятия заказа истекло."
                    ))

        # Закрыть сессию
        asyncio.run(bot_service.close())

        # Если все оферы истекли и заказ не назначен
        if order.status == Order.OrderStatus.SEARCHING:
            assigned_count = order.bookings.filter(status=Booking.Status.ACCEPTED).count()
            if assigned_count == 0:
                # Уведомить клиента
                notify_client.delay(str(order.id), 'all_offers_expired')

        logger.info(f"Expired {expired_count} offers for order {order_id}")
        return {'expired_count': expired_count}

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        return {'success': False, 'error': 'Order not found'}
    except Exception as e:
        logger.error(f"Error expiring offers for order {order_id}: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def notify_client(order_id: str, event_type: str):
    """
    Уведомить клиента о событии

    Args:
        order_id: ID заказа
        event_type: Тип события ('interpreter_accepted', 'all_offers_expired', etc.)
    """
    from apps.models import Order

    try:
        _ = Order.objects.get(id=order_id)

        # TODO: Реализовать отправку email или Telegram уведомления клиенту
        # В зависимости от event_type формировать разные сообщения

        logger.info(f"Client notification sent for order {order_id}, event: {event_type}")
        return {'success': True}

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        return {'success': False, 'error': 'Order not found'}
    except Exception as e:
        logger.error(f"Error notifying client for order {order_id}: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def notify_other_interpreters(order_id: str, accepted_booking_id: str):
    """
    Уведомить остальных переводчиков что заказ принят

    Args:
        order_id: ID заказа
        accepted_booking_id: ID принятого бронирования
    """
    from apps.models import Booking
    from apps.services.telegram_bot import TelegramBotService

    try:
        # Найти все оферы кроме принятого
        bookings = Booking.objects.filter(
            order_id=order_id,
            status=Booking.Status.OFFERED
        ).exclude(id=accepted_booking_id)

        bot_service = TelegramBotService()
        notified_count = 0

        for booking in bookings:
            if booking.interpreter.telegram_chat_id:
                # Отправить уведомление
                success = asyncio.run(bot_service.send_simple_message(
                    chat_id=booking.interpreter.telegram_chat_id,
                    text="ℹ️ Заказ уже принят другим переводчиком."
                ))

                if success:
                    notified_count += 1

                # Отменить офер
                booking.status = Booking.Status.CANCELED
                booking.is_expired = True
                booking.save()

        # Закрыть сессию
        asyncio.run(bot_service.close())

        logger.info(f"Notified {notified_count} interpreters about order {order_id} being taken")
        return {'notified_count': notified_count}

    except Exception as e:
        logger.error(f"Error notifying other interpreters for order {order_id}: {e}")
        return {'success': False, 'error': str(e)}
