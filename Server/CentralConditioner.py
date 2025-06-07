import pymysql
from datetime import datetime, timedelta
from Scheduler import Scheduler


class CentralConditioner:
    def __init__(self):
        self.scheduler = Scheduler(self.get_last_record, self.update_record)  # 实例化调度器

    @staticmethod
    def get_now_costs(room_id, check_out_time):
        costs = 0
        connection = pymysql.connect(host="localhost", user="root", password="123456", database="soft_air")
        cursor = connection.cursor()

        # 先从clients找到这个房间最近一次入住时间
        check_in_time = check_out_time  # 初始化
        cursor.execute("SHOW TABLES LIKE 'clients'")  # 检查表是否存在
        result = cursor.fetchone()
        if result:
            search_checkin_time_query = f"""
                    SELECT 入住时间
                    FROM clients
                    WHERE 房间号 = '{room_id}'
                    ORDER BY 入住时间 DESC
                    LIMIT 1;
                    """
            cursor.execute(search_checkin_time_query)
            res = cursor.fetchone()
            check_in_time = res[0]

        cursor.execute("SHOW TABLES LIKE 'rdr'")  # 检查表是否存在
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
    def get_last_record(number):  # 查询最后一次使用时风速: high, medium, low
        connection = pymysql.connect(host="localhost", user="root", password="123456", database="soft_air")
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES LIKE 'rdr'")  # 检查表是否存在
        result = cursor.fetchone()
        if result:
            search_table_query = f"""
                    SELECT *
                    FROM rdr
                    WHERE 房间号 = '{number}'
                    AND 结束时间 IS NULL
                    ORDER BY 开始时间 DESC
                    LIMIT 1;
                    """
            cursor.execute(search_table_query)
            res = cursor.fetchone()
            connection.commit()
            cursor.close()
            connection.close()
            return res
        return None

    @staticmethod
    def update_record(record, cur_time, cost):
        connection = pymysql.connect(host="localhost", user="root", password="123456", database="soft_air")
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES LIKE 'rdr'")  # 检查表是否存在
        result = cursor.fetchone()
        if result:
            update_query = f"""
                    UPDATE rdr
                    SET 结束时间 = %s, 费用 = %s
                    WHERE 房间号 = %s
                    AND 开始时间 = %s;
                    """
            cursor.execute(update_query, (cur_time, cost, record[0], record[3]))
            connection.commit()
        cursor.close()
        connection.close()

    @staticmethod
    def create_record(number, v, cur_time, now_temperature, target_temperature, mode):
        connection = pymysql.connect(host="localhost", user="root", password="123456", database="soft_air")
        cursor = connection.cursor()
        create_table_query = f"""
                CREATE TABLE IF NOT EXISTS rdr
                (
                `房间号` VARCHAR(64),
                `用户ID` VARCHAR(64),
                `风速` VARCHAR(64),
                `当前温度` DECIMAL(18,2),
                `目标温度` DECIMAL(18,2),
                `冷热模式` VARCHAR(64),
                `开始时间` DATETIME,
                `结束时间` DATETIME,
                `费用` DECIMAL(18,2)
                );
            """
        insert_query = f"""
                INSERT INTO rdr (房间号, 风速, 当前温度, 目标温度, 冷热模式, 开始时间) VALUES (%s, %s, %s, %s, %s, %s);
                """
        cursor.execute(create_table_query)
        cursor.execute(insert_query, (number, v, now_temperature, target_temperature, mode, cur_time))
        connection.commit()
        cursor.close()
        connection.close()

    def create_server(self, room_id, current_room_temp):  # 供PowerOn调用
        pass

    def set_temp_request(self, room_id, target_temp):  # 供ChangeTemp调用
        pass

    def set_speed_request(self, room_id, fan_speed, now_temperature, target_temperature, mode):
        """
        供PowerOn, ChangeTemp, ChangeSpeed调用
        """
        current_time = datetime.now()
        # result = self.get_last_record(room_id)
        # 先调用调度器尝试请求风速服务（核心逻辑）
        result = self.scheduler.update_request(room_id, fan_speed)
        # 如被成功服务或从等待中调度出来，就需要记录数据库
        if result["state"] == "on":
            # 如果之前有记录，先结算旧记录
            last = self.get_last_record(room_id)
            factor = 3
            if last:
                if last[2] == 'high':
                    factor = 1
                elif last[2] == 'medium':
                    factor = 2
                bill = round((current_time - last[3]).total_seconds() / 60 / factor, 2)
                self.update_record(last, current_time, bill)
            # 创建新记录
            self.create_record(room_id, fan_speed, now_temperature, target_temperature, mode, current_time)
            # result["bill"] = bill  # 加入账单字段
        else:  # 加入等待池，不产生账单
            pass

        # 现在开始bill表示用户截止目前应付金额，而非上一段风速金额
        # 这里current_time时显然还没更新上一段，算不了当时的应付价格，再取次时间戳也可能四舍五入而失败
        # 比如current_time是42.5s，我更新完再取是42.6s，但是我存数据表时四舍五入存的43秒，导致上一段更新了也识别不到，所以加1秒把上一段包含进来
        # 不过这样担心以后数据表太大，更新操作1分钟完成不了，可能有待改进，不过这里感觉加个1分钟其实也不影响，先加1秒吧
        result["bill"] = self.get_now_costs(room_id, current_time + timedelta(seconds=1))

        return result

    def delete_server(self, room_id):  # 供PowerOff调用
        current_time = datetime.now()
        # 调用调度器进行服务下线
        self.scheduler.stop_request(room_id)
        # 查找最后服务记录，计算费用
        result = self.get_last_record(room_id)
        factor = 3
        if result:
            if result[2] == 'high':
                factor = 1
            elif result[2] == 'medium':
                factor = 2
            bill = round((current_time - result[3]).total_seconds() / 60 / factor, 2)
            self.update_record(result, current_time, bill)

        # 现在开始bill表示用户截止目前应付金额，而非上一段风速金额
        # 这里current_time时显然还没更新上一段，算不了当时的应付价格，再取次时间戳也可能四舍五入而失败
        # 比如current_time是42.5s，我更新完再取是42.6s，但是我存数据表时四舍五入存的43秒，导致上一段更新了也识别不到，所以加1秒把上一段包含进来
        # 不过这样担心以后数据表太大，更新操作1分钟完成不了，可能有待改进，不过这里感觉加个1分钟其实也不影响，先加1秒吧
        bill = self.get_now_costs(room_id, current_time + timedelta(seconds=1))

        return {"state": "off", "speed": "", "bill": bill}
    
    def tick(self):
        """
        定时器调用，检查调度器状态并更新
        """
        self.scheduler.tick()
        
    @staticmethod
    def get_all_room_info():
        """
        查询 ac_status 表中所有房间的空调状态信息
        """
        connection = pymysql.connect(host="localhost", user="root", password="123456", database="soft_air")
        cursor = connection.cursor()

        query = """
        SELECT `房间号`, `空调状态`, `风速`, `费用`, `工作模式`, `当前温度`, `目标温度`
        FROM ac_status;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        result = []
        for row in rows:
            result.append({
                "room_id": row[0],
                "status": row[1],  # on / off / wait
                "speed": row[2],
                "bill": float(row[3]),
                "mode": row[4],    # cool / heat
                "now_temp": float(row[5]),
                "set_temp": float(row[6])
            })

        return result
