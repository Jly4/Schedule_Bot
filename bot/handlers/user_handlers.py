from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.utils.status import send_status
from bot.utils.utils import status_command, del_pin_message
from bot.utils.schedule import schedule_for_day
from bot.utils.states import ClassState
from bot.utils.school_classes import choose_class_number

router = Router()


@router.message(F.pinned_message != None)
async def pin_schedule_msg(message: Message) -> None:
    """ this func intercept all service messages from a telegram """
    await del_pin_message(message)


@router.message(Command('status'))
async def status_msg(message: Message) -> None:
    await status_command(message)


@router.callback_query(F.data == 'status')
async def status_call(query: CallbackQuery) -> None:
    await send_status(query.message.chat.id)


@router.callback_query(F.data.startswith('schedule_for_day_'))
async def update_schedule_call(query: CallbackQuery) -> None:
    await schedule_for_day(query)


@router.callback_query(F.data.startswith('choose_class'))
async def choose_class_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ClassState.choose_class)
    await choose_class_number(query.message.chat.id)

