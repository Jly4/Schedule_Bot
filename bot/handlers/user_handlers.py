from aiogram import Router, F, types
from aiogram.filters import Command

from bot.utils.status import send_status
from bot.utils.utils import status_command, del_pin_message
from bot.utils.schedule import schedule_for_day

router = Router()


@router.message(F.pinned_message != None)
async def pin_schedule_msg(message: types.Message) -> None:
    """ this func intercept all service messages from a telegram """
    await del_pin_message(message)


@router.message(Command('status'))
async def status_msg(message: types.Message) -> None:
    await status_command(message)


@router.callback_query(F.data == 'status')
async def status_call(callback_query: types.CallbackQuery) -> None:
    await send_status(callback_query.message.chat.id)


@router.callback_query(F.data.startswith('schedule_for_day_'))
async def update_schedule_call(callback_query: types.CallbackQuery) -> None:
    await schedule_for_day(callback_query)

