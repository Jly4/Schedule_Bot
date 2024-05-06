import os
import pytz
from datetime import datetime

from bot.database.database import db
from bot.logs.log_config import custom_logger

local_timezone = pytz.timezone('Asia/Tomsk')


class ScheduleLogic:
    def __init__(self, chat_id: int, cls: str):
        self.chat_id = chat_id
        self.cls = cls

    async def should_regen_img(self, image_path_name: str) -> bool:
        """ if schedule should be regenerated
        1. if schedule_img doesn't exist
        2. if schedule on site was updated
        """
        schedule_exist = os.path.exists(image_path_name)

        if not schedule_exist or await self.schedule_changed():
            return True

        custom_logger.debug(self.chat_id, 'should_regen: False')
        return False

    @staticmethod
    async def schedule_day() -> int:
        local_date = datetime.now(local_timezone)
        day_of_week = local_date.weekday()
        hour = local_date.hour

        if day_of_week == 6:
            return 0  # If today is Sunday, return Monday

        if day_of_week == 5:
            if hour < 10:
                return 5  # If Saturday before 11, return Saturday
            return 0  # If Saturday and hour > 9, return Monday

        if hour > 14:
            return day_of_week + 1  # If after 2 PM, return tomorrow

        return day_of_week  # Otherwise, return today

    async def should_send(self) -> bool:
        """ if schedule should be sent """
        custom_logger.debug(self.chat_id)

        if await self.weekend_filter():
            custom_logger.debug(self.chat_id, '<y>wknd_fltr: <r>True</></>')
            return False

        if await self.today_condition():
            custom_logger.debug(self.chat_id, '<y>today_cond: <r>True</></>')
            return True

        if await self.tomorrow_condition():
            custom_logger.debug(self.chat_id, '<y>tomorrow_cond: <r>True</></>')
            return True

        return False

    @staticmethod
    async def weekend_filter() -> bool:
        """ weekend filter for schedule sending
            if 1 or 2 -> True (skip sending)
            1. if saturday and hour > 9
            2. if sunday and hour < 20
        """
        local_date = datetime.now(local_timezone)
        day_of_week = local_date.weekday()
        hour = local_date.hour

        if day_of_week == 5 and hour >= 10:
            return True

        if day_of_week == 6 and hour < 20:
            return True

        return False

    async def today_condition(self) -> bool:
        """ schedule can be sent for today
            if 1 and 2 and 3 -> True
            1. if schedule on site was updated
            2. if hour < 15,otherwise the schedule for today is not relevant
            3. the schedule for today has been changed
        """
        local_date = datetime.now(local_timezone)
        hour = local_date.hour

        if not await self.time_changed():
            return False

        if hour > 14:
            return False

        if not await self.schedule_changed():
            return False

        return True

    async def tomorrow_condition(self) -> bool:
        """ schedule can be sent for tomorrow
            if all(1, 2, 3, 4, 5) -> True
            1. if hours > 16 (the school day is over)
            2. if not saturday
            3. the schedule for tomorrow has not been printed
            4. if schedule on site been changed or hour > 20
        """
        local_date = datetime.now(local_timezone)
        day_of_week = local_date.weekday()
        hour = local_date.hour

        if hour < 16:
            return False

        if day_of_week == 5:
            return False

        if not await self.time_changed() and hour < 20:
            return False

        if not await self.schedule_changed() and hour < 20:
            return False

        if await self.printed_tomorrow() and not await self.schedule_changed():
            return False

        return True

    async def schedule_changed(self) -> bool:
        """ returns True if the last automatically printed schedule
            is different from the current one
        """
        data = await db.get_data_by_cls(
            self.chat_id,
            self.cls,
            'schedule_json',
            'prev_schedule_json'
        )

        custom_logger.debug(msg=f'\n{data[0]}\n{data[1]}')

        if data[0] != data[1]:
            custom_logger.debug(self.chat_id, '<y>sched_change: <r>True</></>')
            return True

        custom_logger.debug(self.chat_id, '<y>sched_change: <r>False</></>')
        return False

    async def time_changed(self) -> bool:
        """ return True if time of change updated on site """
        data = await db.get_data_by_cls(
            self.chat_id,
            self.cls,
            'schedule_change_time',
            'last_printed_change_time'
        )

        schedule_change_time = data[0]
        last_printed_change_time = data[1]

        if schedule_change_time != last_printed_change_time:
            custom_logger.debug(self.chat_id, '<y>time_changed: <r>True</></>')
            return True

        custom_logger.debug(self.chat_id, '<y>time_changed: <r>False</></>')
        return False

    async def printed_tomorrow(self) -> bool:
        """ returns True if today schedule was printed """
        local_date = datetime.now(local_timezone)
        tomorrow = (local_date.weekday() + 1) % 7

        last_print_day = await db.get_data_by_cls(
            self.chat_id,
            self.cls,
            'last_print_time_day'
        )
        custom_logger.debug(self.chat_id, f'last_print_day {last_print_day}')

        if last_print_day == tomorrow:
            custom_logger.debug(self.chat_id, '<y>printed_tmrw: <r>True</></>')
            return True

        custom_logger.debug(self.chat_id, '<y>printed_tmrw: <r>False</></>')
        return False

    async def printed_today(self) -> bool:
        """ returns True if today schedule was printed """
        local_date = datetime.now(local_timezone)
        today = local_date.day

        last_print_day = await db.get_data_by_cls(
            self.chat_id,
            self.cls,
            'last_print_time_day'
        )

        if last_print_day == today:
            return True
        return False
