import asyncio
import json

from aiogram.types import Update
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.utils import logger


@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(View):
    """Webhook endpoint для Aiogram"""

    def post(self, request):
        """Обработка webhook от Telegram"""
        try:
            # Парсинг update
            update_data = json.loads(request.body)
            update = Update(**update_data)

            # Обработка update через Aiogram dispatcher
            from apps.telegram.bot import bot, dp
            asyncio.run(dp.feed_update(bot, update))

            return HttpResponse(status=200)

        except Exception as e:
            logger.error(f"Error processing Telegram webhook: {e}")
            return HttpResponse(status=500)
