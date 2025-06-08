from datetime import datetime
import sqlite3

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
        self.idle_pool = set()     # 空闲服务对象池

    def get_fan_speed_priority(self, fan_speed):
        """
        获取风速对应的优先级:high=1, medium=2, low=3(数值越小优先级越高)
        """
        return {'high': 1, 'medium': 2, 'low': 3}.get(fan_speed, 99)

    def start_room(self, room_id, fan_speed, now_temperature, target_temperature, mode):
        """
        开始为某个房间送风：调用 CentralConditioner 记录开始送风时间，并加入 active_pool
        """
        now = datetime.now()
        # self.cc.create_record(room_id, fan_speed, now)
        self.active_pool[room_id] = {"fan_speed": fan_speed, "start_time": now}
        # 更新数据库状态：空调开启
        self.update_status(
            room_id=room_id,
            ac_state="on",
            fan_speed=fan_speed,
            current_temp=now_temperature,
            target_temp=target_temperature,
            work_mode=mode,
            cost=0
        )
        

    def stop_room(self, room_id, fan_speed, now_temperature, target_temperature, mode):
        """
        停止某个房间送风：调用 CentralConditioner 结算并更新记录
        """
        # 更新数据库状态：空调关闭
        Scheduler.update_status(
            room_id=room_id,
            ac_state="off",
            fan_speed=fan_speed,
            current_temp=now_temperature,
            target_temp=target_temperature,
            work_mode=mode,
            cost=0
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
                fan_speed = self.active_pool[room_id]["fan_speed"]
                record_ac = self.get_last_record_from_acstatus(room_id)
                self.stop_room(room_id, fan_speed, record_ac[3], record_ac[4], record_ac[6])
                self.waiting_pool[room_id] = {
                    "fan_speed": fan_speed,
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
        fan_speed = self.active_pool[room_id]["fan_speed"]
        
        record_ac = self.get_last_record_from_acstatus(room_id)
        self.stop_room(room_id, fan_speed, record_ac[3], record_ac[4], record_ac[6])
        self.waiting_pool[room_id] = {
            "fan_speed": fan_speed,
            "wait_start": datetime.now(),
            "priority": self.get_fan_speed_priority(fan_speed)
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
            
            record_ac = self.get_last_record_from_acstatus(room_id)
            del self.waiting_pool[room_id]
            self.start_room(room_id, fan_speed, record_ac[3], record_ac[4], record_ac[6])

    def update_request(self, room_id, fan_speed, now_temperature, target_temperature, mode):
        """
        风速变更或开机处理逻辑
        :return: 状态字典 {"state": "on"/"wait", "speed": str, "evicted": room_id}
        """
        new_priority = self.get_fan_speed_priority(fan_speed)

        if room_id in self.active_pool:
            # 正在服务 → 停止旧服务
            self.stop_room(room_id, fan_speed, now_temperature, target_temperature, mode)
            del self.active_pool[room_id]
        elif room_id in self.waiting_pool:
            # 在等待队列中 → 停止旧服务
            del self.waiting_pool[room_id]
        else:
            # 新请求 → 检查空闲池
            if room_id in self.idle_pool:
                self.idle_pool.discard(room_id)

        if len(self.active_pool) < self.max_running:
            # 还有空闲服务位
            self.start_room(room_id, fan_speed, now_temperature, target_temperature, mode)
            return {"state": "on", "speed": fan_speed, "evicted": None}

        # 开始调度逻辑
        evicted = self.evict_by_priority(new_priority)
        if evicted:
            self.start_room(room_id, fan_speed, now_temperature, target_temperature, mode)
            return {"state": "on", "speed": fan_speed, "evicted": evicted}

        # 无法调度 → 放入等待队列
        self.waiting_pool[room_id] = {
            "fan_speed": fan_speed,
            "wait_start": datetime.now(),
            "priority": new_priority
        }
        self.update_status(
            room_id=room_id,
            ac_state="wait",
            fan_speed=fan_speed,
            current_temp=now_temperature,
            target_temp=target_temperature,
            work_mode=mode,
            cost=0
        )
        return {"state": "wait", "speed": fan_speed, "evicted": None}

    def stop_request(self, room_id):
        """
        关机请求处理
        :return: 状态字典 {"state": "off", "speed": "", "bill": 0}
        """
        record_ac = self.get_last_record_from_acstatus(room_id)
        if room_id in self.active_pool:
            fan_speed = self.active_pool[room_id]["fan_speed"]
            self.stop_room(room_id, fan_speed, record_ac[3], record_ac[4], record_ac[6])
            del self.active_pool[room_id]
            self.idle_pool.add(room_id)
            self.assign_waiting_room()
        elif room_id in self.waiting_pool:
            del self.waiting_pool[room_id]
            self.idle_pool.add(room_id)

            record_ac = self.get_last_record_from_acstatus(room_id)

            # 若在等待队列中关机，也应更新状态为 off
            Scheduler.update_status(
                room_id=room_id,
                ac_state="off",
                fan_speed="",
                current_temp="",
                target_temp="",
                work_mode="off",
                cost=0
            )

        return {"state": "off", "speed": "", "bill": record_ac[4] if record_ac else 0}

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
    def create_status():
        """
        创建空调状态表 ac_status 中的记录
        """
        connection = sqlite3.connect("soft_air.db")
        cursor = connection.cursor()
        # 创建 ac_status 表，如果不存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ac_status';")
        result = cursor.fetchone()
        if result:
            return
        # 如果表不存在，则创建
        create_table_query = """
            CREATE TABLE IF NOT EXISTS ac_status (
                `房间号` VARCHAR(64) PRIMARY KEY,
                `空调状态` VARCHAR(64),
                `风速` VARCHAR(64),
                `当前温度` DECIMAL(5,2),
                `目标温度` DECIMAL(5,2),
                `工作模式` VARCHAR(64),
                `费用` DECIMAL(10,2) DEFAULT 0
            );
        """
        cursor.execute(create_table_query)

        connection.commit()
        cursor.close()
        connection.close()

    def update_status(self, room_id, ac_state, fan_speed, current_temp, target_temp, work_mode, cost):
        """
        更新空调状态表 ac_status 中的记录
        """
        connection = sqlite3.connect("soft_air.db")
        cursor = connection.cursor()

        update_query = """
            INSERT OR REPLACE INTO ac_status (房间号, 空调状态, 风速, 当前温度, 目标温度, 工作模式, 费用)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        cursor.execute(update_query, (room_id, ac_state, fan_speed, current_temp, target_temp, work_mode, cost))

        connection.commit()
        cursor.close()
        connection.close()

    def get_last_record_from_acstatus(self, room_id):
        """
        从 ac_status 表获取指定房间的最后一条记录
        """
        connection = sqlite3.connect("soft_air.db")
        cursor = connection.cursor()
        query = "SELECT * FROM ac_status WHERE 房间号 = ? LIMIT 1;"
        cursor.execute(query, (room_id,))
        record = cursor.fetchone() #record
        cursor.close()
        connection.close()
        return record
    
    # 根据前端传来的房间号获取房间空调状态
    def get_room_status(self, room_id):
        record_ac = self.get_last_record_from_acstatus(room_id)
        if record_ac:
            return {
                "state": record_ac[1],
                "speed": record_ac[2],
                "current_temp": record_ac[3],
                "target_temp": record_ac[4],
                "cost": record_ac[5],
                "work_mode": record_ac[6]
            }
        return None
