import logging
from datetime import timedelta
from typing import List

from django.db import transaction
from django.utils import timezone

from apps.models import Booking, Order, OrderInterpreter

logger = logging.getLogger(__name__)


class OrderWorkflowService:
    """Сервис для управления workflow заказа"""

    def __init__(self, order: Order):
        """
        Args:
            order: Экземпляр модели Order
        """
        self.order = order

    def create_and_search(self) -> dict:
        """
        Создать заказ и запустить поиск переводчиков

        Returns:
            dict с результатами поиска
        """
        # Сохранить заказ
        self.order.status = Order.OrderStatus.NEW
        self.order.save()

        # Запустить поиск
        from apps.services.interpreter_search import InterpreterSearchService
        search_service = InterpreterSearchService(self.order)
        interpreters = search_service.find_available_interpreters()

        # Определить количество нужных переводчиков
        # Для синхронного перевода нужно 2 переводчика
        required_count = 2 if self._is_synchronous_translation() else 1

        return {
            'order_id': str(self.order.id),
            'interpreters': interpreters,
            'required_count': required_count,
            'found_count': interpreters.count()
        }

    def send_offers(self, interpreter_ids: List[str]) -> dict:
        """
        Отправить оферы выбранным переводчикам

        Args:
            interpreter_ids: Список ID переводчиков

        Returns:
            dict со статистикой отправки
        """
        from apps.tasks.telegram_tasks import (expire_order_offers,
                                               send_order_offer_notification)

        # Время истечения: текущее время + 3 часа
        expires_at = timezone.now() + timedelta(hours=3)

        sent_count = 0
        for interpreter_id in interpreter_ids:
            # Создать Booking
            booking = Booking.objects.create(
                order=self.order,
                interpreter_id=interpreter_id,
                status=Booking.Status.OFFERED,
                offer_expires_at=expires_at,
                rate=0  # TODO: Рассчитать ставку на основе заказа
            )

            # Отправить Telegram уведомление
            send_order_offer_notification.delay(str(booking.id))
            sent_count += 1

        # Обновить статус заказа
        self.order.status = Order.OrderStatus.SEARCHING
        self.order.save()

        # Запланировать истечение оферов через 3 часа
        expire_order_offers.apply_async(
            args=[str(self.order.id)],
            countdown=3 * 60 * 60  # 3 часа в секундах
        )

        logger.info(f"Sent {sent_count} offers for order {self.order.id}")

        return {
            'sent_count': sent_count,
            'order_status': self.order.status,
            'expires_at': expires_at
        }

    def handle_interpreter_response(self, booking_id: str, accepted: bool) -> dict:
        """
        Обработать ответ переводчика на офер (с database lock для race condition)

        Args:
            booking_id: ID бронирования
            accepted: True если принял, False если отклонил

        Returns:
            dict с результатом обработки
        """
        with transaction.atomic():
            # Получить booking с блокировкой строки
            booking = Booking.objects.select_for_update().get(id=booking_id)

            # Проверить, не истек ли офер
            if booking.is_expired:
                return {'success': False, 'message': 'Время для принятия заказа истекло'}

            booking.responded_at = timezone.now()

            if accepted:
                # Получить заказ с блокировкой
                order = Order.objects.select_for_update().get(id=booking.order_id)

                # Проверить, не принят ли уже заказ
                required_count = 2 if self._is_synchronous_translation() else 1
                current_count = order.interpreters.count()

                if current_count >= required_count:
                    return {'success': False, 'message': 'Заказ уже принят другим переводчиком'}

                # Принять заказ
                booking.status = Booking.Status.ACCEPTED
                booking.save()

                # Создать связь OrderInterpreter
                OrderInterpreter.objects.create(
                    order=order,
                    interpreter=booking.interpreter,
                    rate=booking.rate
                )

                # Обновить статус заказа
                new_count = current_count + 1
                if new_count >= required_count:
                    order.status = Order.OrderStatus.ASSIGNED
                    # Отменить все остальные оферы
                    Booking.objects.filter(
                        order=order,
                        status=Booking.Status.OFFERED
                    ).exclude(id=booking_id).update(
                        status=Booking.Status.CANCELED,
                        is_expired=True
                    )
                else:
                    order.status = Order.OrderStatus.PARTIALLY_ASSIGNED

                order.save()

                # Уведомления
                from apps.tasks.telegram_tasks import (
                    notify_client, notify_other_interpreters)
                notify_client.delay(str(order.id), 'interpreter_accepted')
                if order.status == Order.OrderStatus.ASSIGNED:
                    notify_other_interpreters.delay(str(order.id), str(booking.id))

                logger.info(f"Interpreter {booking.interpreter_id} accepted order {order.id}")
                return {'success': True, 'message': 'Вы приняли заказ!'}

            else:
                # Отклонить заказ
                booking.status = Booking.Status.DECLINED
                booking.save()

                logger.info(f"Interpreter {booking.interpreter_id} declined order {self.order.id}")
                return {'success': True, 'message': 'Вы отклонили заказ'}

    def _is_synchronous_translation(self) -> bool:
        """
        Проверить, является ли заказ синхронным переводом

        Returns:
            bool: True если синхронный перевод
        """
        # Проверить типы перевода заказа
        return self.order.translation_types.filter(name__icontains='synchronous').exists()
