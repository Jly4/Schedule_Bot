import os
import pytz
from datetime import datetime

from bot.database.database import db
from bot.logs.log_config import custom_logger


class ScheduleLogic:
    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self.local_timezone = pytz.timezone('Asia/Tomsk')

    async def should_regen_img(self, image_path_name: str) -> bool:
        """ if schedule should be regenerated
        1. if schedule_img doesn't exist
        2. if schedule on site was updated
        """
        schedule_exist = os.path.exists(image_path_name)

        if not schedule_exist or await self.time_changed():
            return True

        return False

    async def schedule_day(self) -> int:
        custom_logger.debug(self.chat_id)
        local_date = datetime.now(self.local_timezone)
        day_of_week = local_date.weekday()
        hour = local_date.hour

        if day_of_week == 6:
            return 0  # If today is Sunday, return Monday

        if day_of_week == 5:
            if hour < 12:
                return 5  # If Saturday before noon, return Saturday
            return 0  # If Saturday after noon, return Monday

        if hour > 14:
            return day_of_week + 1  # If after 2 PM, return tomorrow

        return day_of_week  # Otherwise, return today

    async def should_send(self) -> bool:
        """ if schedule should be sent """
        custom_logger.debug(self.chat_id)

        if not await self.weekend_condition():
            custom_logger.debug(self.chat_id, '<y>weekend_cond: <r>False</></>')
            return False

        if await self.today_condition():
            custom_logger.debug(self.chat_id, '<y>today_cond: <r>True</></>')
            return True

        if await self.tomorrow_condition():
            custom_logger.debug(self.chat_id, '<y>tomorrow_cond: <r>True</></>')
            return True

        return False

    async def weekend_condition(self) -> bool:
        """ weekend filter for schedule sending
            if not (1 or 2) -> True
            1. if saturday and hour < 12
            2. if sunday and hour > 20
        """
        local_date = datetime.now(self.local_timezone)
        day_of_week = local_date.weekday()
        hour = local_date.hour

        if day_of_week == 5 and hour < 12:
            return False

        if day_of_week == 6 and hour > 20:
            return False

        return True

    async def today_condition(self) -> bool:
        """ schedule can be sent for today
            if 1 and 2 and 3 -> True
            1. if schedule on site was updated
            2. if hour < 15,otherwise the schedule for today is not relevant
            3. the schedule for today has been changed
        """
        local_date = datetime.now(self.local_timezone)
        hour = local_date.hour

        if not await self.time_changed():
            return False

        if hour > 15:
            return False

        if not await self.schedule_changed():
            return False

        return True

    async def tomorrow_condition(self) -> bool:
        """ schedule can be sent for tomorrow
            if all(1, 2, 3, 4, 5) -> True
            1. if hours > 15 (the school day is over)
            2. if not saturday
            3. the schedule for tomorrow has not been printed
            4. if schedule on site been changed or hour > 20
        """
        local_date = datetime.now(self.local_timezone)
        day_of_week = local_date.weekday()
        hour = local_date.hour

        if hour < 15:
            return False

        if day_of_week == 5:
            return False

        if await self.printed_tomorrow():
            return False

        if not await self.schedule_changed() and hour < 20:
            return False

        return True

    async def schedule_changed(self) -> bool:
        """ returns True if the last automatically printed schedule
            is different from the current one
        """
        data_name = ['schedule_json', 'prev_schedule_json']
        data = await db.get_db_data(self.chat_id, *data_name)

        if data[0] != data[1]:
            custom_logger.debug(self.chat_id, '<y>sched_change: <r>True</></>')
            return True

        custom_logger.debug(self.chat_id, '<y>sched_change: <r>False</></>')
        return False

    async def time_changed(self) -> bool:
        """ return True if time of change updated on site """
        data_name = ['schedule_change_time', 'last_printed_change_time']
        data = await db.get_db_data(self.chat_id, *data_name)

        schedule_change_time = data[0]
        last_printed_change_time = data[1]

        if schedule_change_time != last_printed_change_time:
            custom_logger.debug(self.chat_id, '<y>time_changed: <r>True</></>')
            return True

        custom_logger.debug(self.chat_id, '<y>time_changed: <r>False</></>')
        return False

    async def printed_tomorrow(self) -> bool:
        """ returns True if today schedule was printed """
        local_date = datetime.now(self.local_timezone)
        tomorrow = local_date.day + 1

        data_name = ['last_print_time_day', ]
        last_print_day = await db.get_db_data(self.chat_id, *data_name)

        if last_print_day == tomorrow:
            return True
        return False

    async def printed_today(self) -> bool:
        """ returns True if today schedule was printed """
        local_date = datetime.now(self.local_timezone)
        today = local_date.day

        data_name = ['last_print_time_day', ]
        last_print_day = await db.get_db_data(self.chat_id, *data_name)

        if last_print_day == today:
            return True
        return False
