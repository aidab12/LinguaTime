"""
Order Workflow API Views
"""
import json
import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.models import Order

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class OrderCreateView(View):
    """API для создания заказа и поиска переводчиков"""

    def post(self, request):
        """Создать заказ и запустить поиск"""
        try:
            # Парсинг данных формы
            data = json.loads(request.body)

            # Создать заказ
            order = Order.objects.create(
                client=request.user,
                location_type=data['event_type'],
                city_id=data.get('city'),
                address=data.get('address', ''),
                formality_level=data.get('formality_level', Order.FormalityLevel.BUSINESS),
                notes=data.get('details', ''),
                selected_slots=data.get('selected_slots', []),
                start_datetime=data['start_datetime'],
                end_datetime=data['end_datetime']
            )

            # Добавить языки
            if 'languages' in data:
                order.languages.set(data['languages'])

            # Добавить типы перевода
            if 'translation_types' in data:
                order.translation_types.set(data['translation_types'])

            # Запустить поиск
            from apps.services.order_workflow import OrderWorkflowService
            workflow = OrderWorkflowService(order)
            result = workflow.create_and_search()

            return JsonResponse({
                'success': True,
                'order_id': result['order_id'],
                'interpreters': [
                    {
                        'id': str(i.id),
                        'name': i.get_full_name(),
                        'languages': [str(lang) for lang in i.language.all()],
                        'photo': i.photo.url if hasattr(i, 'photo') and i.photo else None
                    }
                    for i in result['interpreters']
                ],
                'required_count': result['required_count']
            })

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class OrderSendOffersView(View):
    """API для отправки оферов выбранным переводчикам"""

    def post(self, request, order_id):
        """Отправить оферы"""
        try:
            data = json.loads(request.body)
            interpreter_ids = data['interpreter_ids']

            order = Order.objects.get(id=order_id, client=request.user)

            from apps.services.order_workflow import OrderWorkflowService
            workflow = OrderWorkflowService(order)
            result = workflow.send_offers(interpreter_ids)

            return JsonResponse({
                'success': True,
                'message': 'Оферы отправлены',
                'sent_count': result['sent_count']
            })

        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Order not found'
            }, status=404)
        except Exception as e:
            logger.error(f"Error sending offers: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
