import sqlite3

from typing import Union

from bot.logs.log_config import custom_logger


class DatabaseClass:
    def __init__(self, location: str):
        self.DB_LOCATION = location
        self.connection = sqlite3.connect(location)
        self.cursor = self.connection.cursor()

    async def database_init(self):
        # create main_table sheet
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_data (
        count INTEGER PRIMARY KEY,
        chat_id INTEGER NOT NULL,
        schedule_auto_send INTEGER DEFAULT 0 NOT NULL,
        bot_enabled INTEGER DEFAULT 1 NOT NULL,
        school_class TEXT DEFAULT 'b11',
        school_change INTEGER DEFAULT 1,
        schedule_json TEXT DEFAULT '',
        del_old_schedule INTEGER DEFAULT 1,
        pin_schedule_message INTEGER DEFAULT 1,
        last_status_message_id INTEGER DEFAULT 0,
        last_schedule_message_id INTEGER DEFAULT 0,
        last_settings_message_id INTEGER DEFAULT 0,
        schedule_change_time TEXT DEFAULT '',
        last_user_activity_time TEXT DEFAULT '',
        last_print_time TEXT DEFAULT 'еще не проверялось',
        last_printed_change_time TEXT DEFAULT 'еще не проверялось',
        last_check_schedule TEXT DEFAULT 'еще не проверялось',
        last_print_time_day INTEGER DEFAULT 0,
        last_print_time_hour INTEGER DEFAULT 0,
        prev_schedule_json TEXT DEFAULT '',
        schedule_bg_color TEXT DEFAULT '255,255,143'
        )
        ''')

        # create index for chat_id column
        self.cursor.execute('''
        CREATE INDEX IF NOT EXISTS
        idx_chat_id ON user_data (chat_id)
        ''')
        self.connection.commit()

    # save db
    async def commit(self):
        self.connection.commit()

    async def add_new_chat_id(self, chat_id: int) -> None:
        custom_logger.debug(chat_id, '<c>new chat_id</>')

        self.cursor.execute('INSERT INTO user_data (chat_id) '
                            'VALUES (?)', (chat_id,))

        self.connection.commit()  # save db

    async def get_db_data(self, chat_id: int, *args: str) -> Union[tuple, int]:
        custom_logger.debug(chat_id, f'get_db_data: <c>{args}</>')

        self.cursor.execute(f'''
            SELECT {", ".join(args)}
            FROM user_data
            WHERE chat_id = {chat_id}
        ''')

        data_list: list = self.cursor.fetchall()
        # if data is empty, user not exists in db, add user_id to db
        if not len(data_list):
            custom_logger.critical(chat_id, '<c>not exist in bd</>')

            from bot.utils.status import send_status
            await self.add_new_chat_id(chat_id)
            await send_status(chat_id, edit=1)
            return await self.get_db_data(chat_id, *args)

        data_tuple: tuple = data_list[0]
        # if only one value, unpack it from tuple
        if len(data_tuple) > 1:
            return data_tuple
        else:
            return data_tuple[0]

    async def update_db_data(self, chat_id: int, **kwargs) -> None:
        custom_logger.debug(chat_id, f'update_db_data: <c>{kwargs.keys()}</>')

        set_args = ", ".join(f"{key} = ?" for key in kwargs)
        values = tuple(kwargs.values())

        self.cursor.execute(f'''
            UPDATE user_data
            SET {set_args}
            WHERE chat_id = ?
        ''', values + (chat_id,))

        self.connection.commit()

    async def get_user_id_list(self) -> list:
        self.cursor.execute('SELECT chat_id FROM user_data')

        user_id_list = [i[0] for i in self.cursor.fetchall()]  # unpack values

        return user_id_list

    async def delete_chat_id(self, chat_id: int) -> None:
        custom_logger.info(chat_id, '<r>Deleted from db</>')

        self.cursor.execute(f'''
        DELETE FROM user_data
        WHERE chat_id = {chat_id};
        ''')

        self.connection.commit()

    async def get_status_msg_id(self, chat_id: int) -> int:
        msg_id = await self.get_db_data(chat_id, 'last_status_message_id')

        return msg_id


db = DatabaseClass('bot/database/bot_data.db')
