import sqlite3
from datetime import datetime


class FrontDesk:
    def __init__(self):
        self.rooms = ['101', '102', '103', '104', '105', '106', '107', '108', '109', '110',
                      '201', '202', '203', '204', '205', '206', '207', '208', '209', '210']

    @staticmethod
    def get_busy_rooms():
        busy_rooms = set()
        connection = sqlite3.connect("soft_air.db")
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients';")  # 检查表是否存在
        result = cursor.fetchone()
        if result:
            search_table_query = f"""
                    SELECT 房间号
                    FROM clients
                    WHERE 结账时间 is NULL;
                    """
            cursor.execute(search_table_query)
            res = cursor.fetchall()
            for row in res:
                busy_rooms.add(row[0])
        cursor.close()
        connection.close()
        return list(busy_rooms)

    @staticmethod
    def get_all_cost(room_id, check_in_time, check_out_time):
        costs = 0
        connection = sqlite3.connect("soft_air.db")
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rdr';")  # 检查表是否存在
        result = cursor.fetchone()
        if result:
            search_table_query = f"""
                    SELECT 费用
                    FROM rdr
                    WHERE 房间号 = '{room_id}'
                    AND 开始时间 >= '{check_in_time}'
                    AND 结束时间 <= '{check_out_time}';
                    """
            cursor.execute(search_table_query)
            res = cursor.fetchall()
            for row in res:
                costs += row[0]
        cursor.close()
        connection.close()
        return float(costs)

    @staticmethod
    def get_last_record(room_id):  # 查询最后一次使用时风速: high, medium, low
        connection = sqlite3.connect("soft_air.db")
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rdr';")  # 检查表是否存在
        result = cursor.fetchone()
        if result:
            search_table_query = f"""
                    SELECT *
                    FROM rdr
                    WHERE 房间号 = ?
                    AND 结束时间 IS NULL
                    ORDER BY 开始时间 DESC
                    LIMIT 1;
                    """
            cursor.execute(search_table_query, (room_id,))
            res = cursor.fetchone()
            connection.commit()
            cursor.close()
            connection.close()
            return res
        return None

    @staticmethod
    def update_record(record, cur_time, cost):
        connection = sqlite3.connect("soft_air.db")
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rdr';")  # 检查表是否存在
        result = cursor.fetchone()
        if result:
            update_query = f"""
                    UPDATE rdr
                    SET 结束时间 = ?, 费用 = ?
                    WHERE 房间号 = ?
                    AND 开始时间 = ?;
                    """
            cursor.execute(update_query, (cur_time, cost, record[0], record[6]))
            connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def get_time(user_name):
        times = []
        connection = sqlite3.connect("soft_air.db")
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients';")  # 检查表是否存在
        result = cursor.fetchone()
        if result:
            search_table_query = f"""
                        SELECT 入住时间, 结账时间
                        FROM clients
                        WHERE 用户名 = ?
                        ORDER BY 入住时间 DESC
                        LIMIT 1;
                        """
            cursor.execute(search_table_query, (user_name,))
            res = cursor.fetchall()
            for row in res:
                times.append({'check_in_time': row[0], 'check_out_time': row[1]})
        cursor.close()
        connection.close()
        return times[0]

    def get_status(self):
        rooms = []
        busy_rooms = self.get_busy_rooms()
        for room in self.rooms:
            if room in busy_rooms:
                rooms.append({"roomId": room, "status": "busy"})
            else:
                rooms.append({"roomId": room, "status": "free"})
        return {"rooms": rooms}

    def turn_off_ac(self, room_id, turn_off_time):
        # current_time = datetime.now()
        result = self.get_last_record(room_id)
        factor = 3  # 冷启动时风速为低, 3分钟1元
        if result:
            if result[2] == 'high':
                factor = 1
            elif result[2] == 'medium':
                factor = 2
            bill = round((turn_off_time - result[3]).total_seconds() / 60 / factor, 2)
            self.update_record(result, turn_off_time, bill)

    def open_room(self, customer_name, customer_id, room_id, current_time):
        connection = sqlite3.connect("soft_air.db")
        cursor = connection.cursor()
        create_table_query = f"""
                            CREATE TABLE IF NOT EXISTS clients
                            (
                            `用户名` VARCHAR(64),
                            `用户ID` VARCHAR(64),
                            `房间号` VARCHAR(64),
                            `入住时间` DATETIME,
                            `结账时间` DATETIME,
                            `总费用` DECIMAL(18,2)
                            );
                        """
        insert_query = f"""
                            INSERT INTO clients (用户名, 用户ID, 房间号, 入住时间) VALUES (?, ?, ?, ?)
                            """
        cursor.execute(create_table_query)
        cursor.execute(insert_query, (customer_name, customer_id, room_id, current_time))
        connection.commit()
        cursor.close()
        connection.close()

        # 开房时空调可能正在使用，要关掉，避免给用户多计费
        self.turn_off_ac(room_id, current_time)

    def create_accommodation_order(self, customer_name, customer_id, room_id=0):  # 供Register_CustomerInfo调用
        current_time = datetime.now()
        busy_rooms = self.get_busy_rooms()
        if room_id == 0:
            available_rooms = list(set(self.rooms) - set(busy_rooms))
            if len(available_rooms) != 0:
                self.open_room(customer_name, customer_id, available_rooms[0], current_time)
                return {"status": "OK", "allocate_room": str(available_rooms[0])}
            return {"status": "ERROR", "allocate_room": ""}
        else:
            if room_id in busy_rooms:
                return {"status": "ERROR", "allocate_room": ""}
            else:
                self.open_room(customer_name, customer_id, room_id, current_time)
                return {"status": "OK", "allocate_room": str(room_id)}

    def query_fee_records(self, roomId):  # 供Process_CheckOut调用
        current_time = datetime.now()
        connection = sqlite3.connect("soft_air.db")
        cursor = connection.cursor()
        search_table_query = f"""
                SELECT 入住时间
                FROM clients
                WHERE 房间号 = ?
                ORDER BY 入住时间 DESC;
                """
        cursor.execute(search_table_query, (roomId,))
        res = cursor.fetchone()
        costs = 0
        room_id = ""
        if len(res) != 0:
            check_in_time = res[0]
            room_id = roomId
            check_out_time = current_time
            costs = self.get_all_cost(room_id, check_in_time, check_out_time)
            # 生成账单详单
            update_query = f"""
                    UPDATE clients
                    SET 结账时间 = ?, 总费用 = ?
                    WHERE 房间号 = ?
                    AND 入住时间 = ?;
                    """
            cursor.execute(update_query, (check_out_time, costs, room_id, check_in_time))
            connection.commit()
        cursor.close()
        connection.close()

        # 退房时空调可能正在使用，要关掉，避免给用户少计费
        if room_id != "":
            self.turn_off_ac(room_id, current_time)

        return {"bill": costs}
