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
        school_class TEXT DEFAULT 'b111',
        schedule_json TEXT DEFAULT '',
        del_old_schedule INTEGER DEFAULT 1,
        pin_schedule_message INTEGER DEFAULT 1,
        last_status_message_id INTEGER DEFAULT 1,
        last_schedule_message_id TEXT DEFAULT '',
        schedule_change_time TEXT DEFAULT '',
        last_print_time TEXT DEFAULT '',
        last_printed_change_time TEXT DEFAULT '',
        last_check_schedule TEXT DEFAULT '',
        last_print_time_day TEXT DEFAULT '',
        last_print_time_hour TEXT DEFAULT '',
        prev_schedule_json TEXT DEFAULT '',
        schedule_bg_color TEXT DEFAULT '255,255,143',
        autosend_classes TEXT DEFAULT ''
        )
        ''')

        # create main_table sheet
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_parameters (
        count INTEGER PRIMARY KEY,
        suspend_date TEXT DEFAULT '',
        suspend_bot INTEGER DEFAULT 0
        )
        ''')

        # create index for chat_id column
        self.cursor.execute('''
        CREATE INDEX IF NOT EXISTS
        idx_chat_id ON user_data (chat_id)
        ''')

        # Проверка наличия записей в таблице
        self.cursor.execute(
            'SELECT COUNT(*) FROM bot_parameters'
        )
        result = self.cursor.fetchone()[0]

        # Если таблица пуста, вставляем новую запись
        if result == 0:
            self.cursor.execute(
                "INSERT INTO bot_parameters (suspend_date) VALUES ('')"
            )

        self.connection.commit()
        
    # save db
    async def commit(self):
        self.connection.commit()

    async def add_new_chat_id(self, chat_id: int) -> None:
        custom_logger.debug(chat_id, '<c>new chat_id</>', depth=2)

        self.cursor.execute(
            'INSERT INTO user_data (chat_id) VALUES (?)', (chat_id,))

        self.connection.commit()  # save db

    async def get_db_data(
            self,
            chat_id: int,
            *args: str
    ) -> Union[tuple, int, str]:
        custom_logger.debug(chat_id, f'get_db_data: <c>{args}</>', depth=2)

        self.cursor.execute(f'''
            SELECT {", ".join(args)}
            FROM user_data
            WHERE chat_id = {chat_id}
        ''')

        data_list: list = self.cursor.fetchall()
        # if data is empty, user not exists in db, add user_id to db
        if not len(data_list):
            custom_logger.critical(chat_id, '<c>not exist in bd</>')
            await self.user_not_exist(chat_id, args)
            return 0

        else:
            data_tuple: tuple = data_list[0]
            # if only one value, unpack it from tuple
            if len(data_tuple) > 1:
                return data_tuple
            else:
                return data_tuple[0]

    async def user_not_exist(self, chat_id: int, args: object) -> None:
        """ If this func has been called from activity check -> return
            if it was called from user
            which not exists in db -> send keyboard
        """
        if 'bot_enabled' in args:
            return

        else:
            from bot.utils.school_classes import choose_class_number
            await self.add_new_chat_id(chat_id)
            await choose_class_number(chat_id)

    async def update_db_data(self, chat_id: int, **kwargs) -> None:
        """ update data in db by column name, where chat_id in db == chat_id

        :param chat_id: telegram chat id
        :param kwargs: column_name: 'data'
        :return: None
        """
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
        self.cursor.execute(
            'SELECT chat_id FROM user_data'
        )

        user_id_list = [i[0] for i in self.cursor.fetchall()]  # unpack values

        return user_id_list

    async def delete_chat_id(self, chat_id: int) -> None:
        custom_logger.info(chat_id, '<r>deleting from db</>', depth=2)

        self.cursor.execute(f'''
            DELETE FROM user_data
            WHERE chat_id = {chat_id};
        ''')

        self.connection.commit()

    async def get_status_msg_id(self, chat_id: int) -> int:
        custom_logger.debug(chat_id, depth=2)

        msg_id = await self.get_db_data(chat_id, 'last_status_message_id')

        return msg_id

    async def get_data_by_cls(
            self,
            chat_id: int,
            cls: str,
            *args: str
    ) -> Union[str, int, tuple]:
        data = await self.get_db_data(chat_id, *args)
        data = data if isinstance(data, tuple) else (data, )
        dict_lis = [eval(str_dict) if str_dict else {} for str_dict in data]

        if len(dict_lis) > 1:
            return tuple(dct.get(cls, '') for dct in dict_lis)

        else:
            return dict_lis[0].get(cls, '')

    async def update_data_by_cls(
            self,
            chat_id: int,
            cls: str,
            **kwargs: dict
    ) -> None:
        args = [key for key in kwargs]
        data = await self.get_db_data(chat_id, *args)
        data = data if isinstance(data, tuple) else (data, )

        dict_lis = [eval(str_dict) if str_dict else {} for str_dict in data]
        values = tuple(kwargs.values())
        keys = tuple(kwargs.keys())

        for i in range(len(values)):
            dict_lis[i][cls] = values[i]

        res_dict = dict.fromkeys(keys)
        for i, key in enumerate(keys):
            res_dict[key] = f'{dict_lis[i]}'

        await self.update_db_data(chat_id, **res_dict)

    """ bot_parameters table
    """
    async def turn_suspend_bot(self, user_id: int) -> None:
        custom_logger.debug(user_id, depth=1)

        self.cursor.execute('SELECT suspend_bot FROM bot_parameters')
        suspend_bot = self.cursor.fetchall()[0][0]

        if suspend_bot:
            suspend_bot = 0
        else:
            suspend_bot = 1

        self.cursor.execute(f'''
            UPDATE bot_parameters
            SET suspend_bot = {suspend_bot}
            WHERE count = '1'
        ''')

        self.connection.commit()

    async def get_dev_data(self, *args) -> Union[int, tuple]:
        self.cursor.execute(f'''
                SELECT {", ".join(args)}
                FROM bot_parameters
                WHERE count = '1'
        ''')

        data_tuple: tuple = self.cursor.fetchall()[0]
        # if only one value, unpack it from tuple
        if len(data_tuple) > 1:
            return data_tuple
        else:
            return data_tuple[0]

    async def update_dev_data(self, **kwargs) -> None:
        set_args = ", ".join(f"{key} = ?" for key in kwargs)
        values = tuple(kwargs.values())

        self.cursor.execute(f'''
            UPDATE bot_parameters
            SET {set_args}
            WHERE count = '1'
        ''', values)

        self.connection.commit()


db = DatabaseClass('bot/database/bot_data.db')
