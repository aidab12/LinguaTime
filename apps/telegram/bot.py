from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from django.conf import settings

from apps.utils import logger

# Создание бота и диспетчера
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
router = Router()


# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start для связывания аккаунта"""
    await message.answer(
        "Добро пожаловать в LinguaTime Bot!\n\n"
        "Для связывания вашего аккаунта переводчика, пожалуйста, "
        "перейдите в профиль на сайте и нажмите 'Связать Telegram'.\n\n"
        f"Ваш Chat ID: <code>{message.chat.id}</code>",
        parse_mode='HTML'
    )


# Обработчик callback от inline кнопок
@router.callback_query(lambda c: c.data and (
        c.data.startswith('accept_order:') or c.data.startswith('decline_order:')
))
async def process_order_callback(callback: CallbackQuery):
    """Обработка принятия/отклонения заказа"""
    from apps.models import Booking
    from apps.services.order_workflow import OrderWorkflowService

    action, booking_id = callback.data.split(':')

    try:
        booking = Booking.objects.get(id=booking_id)
        workflow = OrderWorkflowService(booking.order)

        accepted = (action == 'accept_order')
        result = workflow.handle_interpreter_response(booking_id, accepted)

        # Ответить на callback
        await callback.answer(result['message'], show_alert=True)

        # Обновить сообщение (убрать кнопки если успешно)
        if result['success'] and accepted:
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.edit_text(
                callback.message.text + "\n\n✅ <b>Вы приняли этот заказ</b>",
                parse_mode='HTML'
            )
        elif result['success'] and not accepted:
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.edit_text(
                callback.message.text + "\n\n❌ <b>Вы отклонили этот заказ</b>",
                parse_mode='HTML'
            )

    except Booking.DoesNotExist:
        await callback.answer("Заказ не найден", show_alert=True)
    except Exception as e:
        logger.error(f"Error processing callback: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)


# Регистрация роутера
dp.include_router(router)
