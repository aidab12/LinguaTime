import logging
from datetime import datetime
from typing import List

from django.db.models import Q, QuerySet

from apps.models import Interpreter, Order

logger = logging.getLogger(__name__)


class InterpreterSearchService:
    """Сервис для поиска доступных переводчиков на основе требований заказа"""

    def __init__(self, order: Order):
        """
        Args:
            order: Экземпляр модели Order
        """
        self.order = order

    def find_available_interpreters(self) -> QuerySet:
        """
        Находит переводчиков доступных для данного заказа

        Порядок фильтрации:
        1. Языки (должны совпадать все языки заказа)
        2. Типы перевода
        3. Локация (город для onsite, любой для online)
        4. Доступность (исключить занятых)
        5. Пол (если указан)

        Returns:
            QuerySet с доступными переводчиками, отсортированными по приоритету
        """
        # Начать с всех модерированных переводчиков
        queryset = Interpreter.objects.filter(is_moderated=True, is_active=True)

        # Применить фильтры
        queryset = self._filter_by_languages(queryset)
        queryset = self._filter_by_translation_types(queryset)
        queryset = self._filter_by_location(queryset)
        queryset = self._filter_by_availability(queryset)
        queryset = self._filter_by_gender(queryset)

        # Сортировка по приоритету (можно добавить рейтинг, опыт и т.д.)
        queryset = queryset.distinct()

        logger.info(f"Found {queryset.count()} available interpreters for order {self.order.id}")
        return queryset

    def _filter_by_languages(self, queryset: QuerySet) -> QuerySet:
        """
        Фильтрация по языкам

        Переводчик должен владеть всеми языками из заказа

        Args:
            queryset: QuerySet переводчиков

        Returns:
            Отфильтрованный QuerySet
        """
        order_languages = self.order.languages.all()

        if not order_languages.exists():
            return queryset

        # Переводчик должен владеть всеми языками заказа
        for language in order_languages:
            queryset = queryset.filter(language=language)

        return queryset

    def _filter_by_translation_types(self, queryset: QuerySet) -> QuerySet:
        """
        Фильтрация по типам перевода

        Args:
            queryset: QuerySet переводчиков

        Returns:
            Отфильтрованный QuerySet
        """
        translation_types = self.order.translation_types.all()

        if not translation_types.exists():
            return queryset

        # Переводчик должен владеть хотя бы одним типом перевода из заказа
        queryset = queryset.filter(translation_type__in=translation_types)

        return queryset

    def _filter_by_location(self, queryset: QuerySet) -> QuerySet:
        """
        Фильтрация по локации

        Для onsite заказов - переводчики из того же города
        Для online заказов - все переводчики

        Args:
            queryset: QuerySet переводчиков

        Returns:
            Отфильтрованный QuerySet
        """
        if self.order.location_type == Order.LocationType.ONSITE:
            if self.order.city:
                queryset = queryset.filter(city=self.order.city)
            else:
                # Если город не указан для onsite, вернуть пустой queryset
                return queryset.none()

        # Для online заказов не фильтруем по локации
        return queryset

    def _filter_by_availability(self, queryset: QuerySet) -> QuerySet:
        """
        Исключить переводчиков с конфликтующими записями Availability

        Для каждого временного слота заказа проверяем пересечение с BUSY записями

        Args:
            queryset: QuerySet переводчиков

        Returns:
            Отфильтрованный QuerySet
        """
        # Получить все временные диапазоны из выбранных слотов
        slot_ranges = self._convert_slots_to_datetime_ranges(self.order.selected_slots)

        if not slot_ranges:
            # Если нет слотов, использовать start_datetime и end_datetime
            slot_ranges = [{
                'start': self.order.start_datetime,
                'end': self.order.end_datetime
            }]

        # Построить Q объект для проверки пересечений
        conflicts = Q()
        for slot_range in slot_ranges:
            conflicts |= Q(
                availabilities__type='BUSY',
                availabilities__start_datetime__lt=slot_range['end'],
                availabilities__end_datetime__gt=slot_range['start']
            )

        # Исключить переводчиков с конфликтами
        return queryset.exclude(conflicts)

    def _filter_by_gender(self, queryset: QuerySet) -> QuerySet:
        """
        Фильтрация по предпочтению пола (если указано)

        Args:
            queryset: QuerySet переводчиков

        Returns:
            Отфильтрованный QuerySet
        """
        if hasattr(self.order, 'gender_requirement'):
            if self.order.gender_requirement != Order.GenderRequirement.NO_PREFERENCE:
                queryset = queryset.filter(gender=self.order.gender_requirement)

        return queryset

    def _convert_slots_to_datetime_ranges(self, selected_slots: List[str]) -> List[dict]:
        """
        Преобразует слоты в список datetime диапазонов

        Args:
            selected_slots: List[str] - например ['2024-01-15-morning', '2024-01-15-evening']

        Returns:
            List[dict] - список с start и end datetime для каждого слота
        """
        if not selected_slots:
            return []

        SLOT_TIMES = {
            'morning': ('09:00', '14:00'),
            'evening': ('14:00', '18:00')
        }

        ranges = []
        for slot in selected_slots:
            try:
                # Разделить дату и период
                date_str, period = slot.rsplit('-', 1)
                start_time, end_time = SLOT_TIMES.get(period, ('09:00', '18:00'))

                # Создать datetime объекты
                start_datetime = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M")
                end_datetime = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %H:%M")

                ranges.append({
                    'start': start_datetime,
                    'end': end_datetime
                })
            except Exception as e:
                logger.error(f"Error parsing slot {slot}: {e}")
                continue

        return ranges
