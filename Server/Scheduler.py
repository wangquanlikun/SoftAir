from datetime import datetime
import pymysql

class Scheduler:
    def __init__(self, get_last_record, update_record, max_running=10, wait_seconds=10):
        """
        初始化调度器
        :param max_running: 同时最多服务的房间数
        :param wait_seconds: 等待队列时间片长度（秒）
        """
        self.max_running = max_running
        self.wait_seconds = wait_seconds
        self.get_last_record = get_last_record
        self.update_record = update_record

        self.active_pool = {}   # 正在送风的房间 {room_id: {"fan_speed": str, "start_time": datetime}}
        self.waiting_pool = {}  # 等待队列 {room_id: {"fan_speed": str, "wait_start": datetime, "priority": int}}

    def get_fan_speed_priority(self, fan_speed):
        """
        获取风速对应的优先级:high=1, medium=2, low=3(数值越小优先级越高)
        """
        return {'high': 1, 'medium': 2, 'low': 3}.get(fan_speed, 99)

    def start_room(self, room_id, fan_speed):
        """
        开始为某个房间送风：调用 CentralConditioner 记录开始送风时间，并加入 active_pool
        """
        now = datetime.now()
        # self.cc.create_record(room_id, fan_speed, now)
        self.active_pool[room_id] = {"fan_speed": fan_speed, "start_time": now}

         # 更新数据库状态：空调开启
        Scheduler.create_or_update_status(
            room_id=room_id,
            ac_state="on",
            fan_speed=fan_speed,
            current_temp=25.0,  # TODO: 从外部系统获取当前温度
            target_temp=22.0,   # TODO: 从请求中获取目标温度
            cost=0.0,           # 开机时费用为0
            work_mode="cool"    # TODO: 从请求中获取工作模式
        )

    def stop_room(self, room_id):
        """
        停止某个房间送风：调用 CentralConditioner 结算并更新记录
        """
        now = datetime.now()
        record = self.get_last_record(room_id)
        if record:
            factor = {"high": 1, "medium": 2, "low": 3}.get(record[2], 3)
            bill = round((now - record[3]).total_seconds() / 60 / factor, 2)
            self.update_record(record, now, bill)

             # 更新数据库状态：空调关闭
            Scheduler.create_or_update_status(
                room_id=room_id,
                ac_state="off",
                fan_speed=record[2],
                current_temp=25.0,  # TODO: 从外部系统获取
                target_temp=22.0,   # TODO: 从 record 或请求中获取
                cost=bill,
                work_mode="cool"
            )

    def evict_by_priority(self, new_priority):
        """
        基于优先级调度：尝试淘汰一个比新请求优先级低的活跃房间
        :return: 被淘汰的房间ID 或 None
        """
        candidates = []
        for room_id, info in self.active_pool.items():
            priority = self.get_fan_speed_priority(info["fan_speed"])
            candidates.append((priority, info["start_time"], room_id))
        candidates.sort(reverse=True)  # 优先淘汰优先级低 + 时间长的

        for priority, start_time, room_id in candidates:
            if priority > new_priority:
                self.stop_room(room_id)
                self.waiting_pool[room_id] = {
                    "fan_speed": self.active_pool[room_id]["fan_speed"],
                    "wait_start": datetime.now(),
                    "priority": priority
                }
                del self.active_pool[room_id]
                return room_id
        return None

    def evict_by_time(self):
        """
        当风速相等时使用时间片调度：淘汰服务时间最长的房间
        """
        if not self.active_pool:
            return None
        longest = max(self.active_pool.items(), key=lambda x: x[1]["start_time"])
        room_id = longest[0]
        self.stop_room(room_id)
        self.waiting_pool[room_id] = {
            "fan_speed": self.active_pool[room_id]["fan_speed"],
            "wait_start": datetime.now(),
            "priority": self.get_fan_speed_priority(self.active_pool[room_id]["fan_speed"])
        }
        del self.active_pool[room_id]
        return room_id

    def assign_waiting_room(self):
        """
        检查等待队列中是否有等待时间已满的房间，分配空闲服务对象给其送风
        """
        now = datetime.now()
        eligible = []
        for room_id, info in self.waiting_pool.items():
            elapsed = (now - info["wait_start"]).total_seconds()
            if elapsed >= self.wait_seconds:
                eligible.append((info["priority"], info["wait_start"], room_id))

        if eligible:
            eligible.sort()  # 优先选等待最久、优先级最高的
            _, _, room_id = eligible[0]
            fan_speed = self.waiting_pool[room_id]["fan_speed"]
            del self.waiting_pool[room_id]
            self.start_room(room_id, fan_speed)

    def update_request(self, room_id, fan_speed):
        """
        风速变更或开机处理逻辑
        :return: 状态字典 {"state": "on"/"wait", "speed": str, "evicted": room_id}
        """
        new_priority = self.get_fan_speed_priority(fan_speed)

        if room_id in self.active_pool:
            # 正在服务 → 停止旧服务
            self.stop_room(room_id)
            del self.active_pool[room_id]

        if len(self.active_pool) < self.max_running:
            # 还有空闲服务位
            self.start_room(room_id, fan_speed)
            return {"state": "on", "speed": fan_speed, "evicted": None}

        # 开始调度逻辑
        evicted = self.evict_by_priority(new_priority)
        if evicted:
            self.start_room(room_id, fan_speed)
            return {"state": "on", "speed": fan_speed, "evicted": evicted}

        # 无法调度 → 放入等待队列
        self.waiting_pool[room_id] = {
            "fan_speed": fan_speed,
            "wait_start": datetime.now(),
            "priority": new_priority
        }
        return {"state": "wait", "speed": fan_speed, "evicted": None}

    def stop_request(self, room_id):
        """
        关机请求处理
        :return: 状态字典 {"state": "off", "speed": "", "bill": 0}
        """
        if room_id in self.active_pool:
            # self.stop_room(room_id)
            del self.active_pool[room_id]
            self.assign_waiting_room()
        elif room_id in self.waiting_pool:
            del self.waiting_pool[room_id]

            # 若在等待队列中关机，也应更新状态为 off
            Scheduler.create_or_update_status(
                room_id=room_id,
                ac_state="off",
                fan_speed="",
                current_temp=25.0,  # TODO: 获取真实值
                target_temp=22.0,
                cost=0.0,
                work_mode="cool"
            )

        return {"state": "off", "speed": "", "bill": 0}

    def tick(self):
        """
        每秒调用一次，用于处理时间片调度逻辑（等待时长满则尝试调度）
        """
        self.assign_waiting_room()

    def get_status(self):
        """
        返回当前活跃和等待队列的状态信息
        """
        return {
            "active": {
                k: {
                    "fan_speed": v["fan_speed"],
                    "start_time": v["start_time"].strftime("%H:%M:%S")
                } for k, v in self.active_pool.items()
            },
            "waiting": {
                k: {
                    "fan_speed": v["fan_speed"],
                    "wait_start": v["wait_start"].strftime("%H:%M:%S"),
                    "priority": v["priority"]
                } for k, v in self.waiting_pool.items()
            }
        }
    
    @staticmethod
    def create_or_update_status(room_id, ac_state, fan_speed, current_temp, target_temp, cost, work_mode):
        """
        创建或更新空调状态表 ac_status 中的记录
        """
        # 自动判断工作模式
        if current_temp > target_temp:
            work_mode = "cool"
        elif current_temp < target_temp:
            work_mode = "heat"

        connection = pymysql.connect(host="localhost", user="root", password="123456", database="soft_air")
        cursor = connection.cursor()

        create_table_query = """
            CREATE TABLE IF NOT EXISTS ac_status (
                `房间号` VARCHAR(64) PRIMARY KEY,
                `空调状态` VARCHAR(64),
                `风速` VARCHAR(64),
                `当前温度` DECIMAL(5,2),
                `目标温度` DECIMAL(5,2),
                `费用` DECIMAL(18,2),
                `工作模式` VARCHAR(64)
            );
        """
        cursor.execute(create_table_query)

        # 尝试更新已有记录
        update_query = """
            UPDATE ac_status
            SET `空调状态` = %s,
                `风速` = %s,
                `当前温度` = %s,
                `目标温度` = %s,
                `费用` = %s,
                `工作模式` = %s
            WHERE `房间号` = %s;
        """
        cursor.execute(update_query, (ac_state, fan_speed, current_temp, target_temp, cost, room_id))

        if cursor.rowcount == 0:
            # 若没有更新成功（说明该房间记录不存在），则插入新记录
            insert_query = """
                INSERT INTO ac_status (`房间号`, `空调状态`, `风速`, `当前温度`, `目标温度`, `费用`, `工作模式`)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(insert_query, (room_id, ac_state, fan_speed, current_temp, target_temp, cost, work_mode))

        connection.commit()
        cursor.close()
        connection.close()
