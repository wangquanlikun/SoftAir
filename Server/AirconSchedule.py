import sqlite3
import datetime
import threading
import time
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ScheduleRoom:
    def __init__(self, ID, state, fan_speed, mode, set_temp, now_temp, running_time=0, billing_time=0, waiting_time=0):
        self.ID = ID
        self.state = state # 'running' or 'waiting' or 'off'
        self.fan_speed = fan_speed # 0: Low, 1: Medium, 2: High
        self.running_time = running_time # in seconds
        self.waiting_time = waiting_time
        self.billing_time = billing_time
        self.mode = mode # 'cool' or 'heat'
        self.set_temp = set_temp
        self.now_temp = now_temp

class Scheduler:
    def __init__(self, room_ws):
        self.room_ws = room_ws

        self.serving_queue = []
        self.waiting_queue = []

        self.MAX_SERVING = 3  # 最大同时服务的房间数
        self.CIRCULATION_INTERVAL = 19.8  # 时间片间隔（模拟2min）

        self.low_per_minute = 2.0  # 每分钟的低速费用（6倍率）
        self.medium_per_minute = 3.0  # 每分钟的中速费用（6倍率）
        self.high_per_minute = 6.0  # 每分钟的高速费用（6倍率）

        self.database = None
        self.cursor = None

        self.this_thread_database = sqlite3.connect('database.db')
        self.this_thread_cursor = self.this_thread_database.cursor()

        # 创建一个线程池用于处理异步任务
        self.executor = ThreadPoolExecutor(max_workers=5)
        # 创建一个事件循环用于发送消息
        self.loop = asyncio.new_event_loop()
        self.message_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.message_thread.start()

    def _run_event_loop(self):
        """在单独的线程中运行事件循环"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def add_bill(self, roomId, bill):
        bill += self.search_bill(roomId)  # 累加当前账单
        self.cursor.execute('''UPDATE ROOM SET bill = ? WHERE roomId = ?''', (bill, roomId))
        self.database.commit()

    def update_request(self, roomId, set_temp, now_temp, mode):
        for room in self.serving_queue:
            if room.ID == roomId:
                room.set_temp = set_temp
                room.now_temp = now_temp
                room.mode = mode
        for room in self.waiting_queue:
            if room.ID == roomId:
                room.set_temp = set_temp
                room.now_temp = now_temp
                room.mode = mode

    def request_off(self, roomId):
        for room in self.serving_queue:
            if room.ID == roomId:
                self.serving_queue.remove(room)
        for room in self.waiting_queue:
            if room.ID == roomId:
                self.waiting_queue.remove(room)

    def request_on(self, roomId, speed, set_temp, now_temp, mode):
        # 首先检查是否已经在其中，在其中需要当作一次新的请求（移除后再考虑）
        for room in self.serving_queue:
            if room.ID == roomId:
                self.serving_queue.remove(room)
        for room in self.waiting_queue:
            if room.ID == roomId:
                self.waiting_queue.remove(room)

        # 创建新的房间请求
        new_room = ScheduleRoom(roomId, 'running', speed, mode, set_temp, now_temp)

        # 如果服务队列未满，直接加入服务队列
        if len(self.serving_queue) < self.MAX_SERVING:
            self.serving_queue.append(new_room)
            return True

        # 如果服务队列已满，尝试优先级调度
        replace_rooms = []
        # 先查找风速比新请求低的房间
        for i, room in enumerate(self.serving_queue):
            if room.fan_speed < speed:
                replace_rooms.append((i, room))

        if len(replace_rooms) == 0:
            can_wait = False
            for i, room in enumerate(self.serving_queue):
                if room.fan_speed == speed:
                    can_wait = True
                    break

            if can_wait:
                new_room.state = 'waiting'
                new_room.waiting_time = self.CIRCULATION_INTERVAL
                self.waiting_queue.append(new_room)
                return False
            else:
                return False
        elif len(replace_rooms) == 1:
            # 只有一个可抢占的房间，直接替换
            index, longest_serving = replace_rooms[0]
            longest_serving.state = 'waiting'
            longest_serving.waiting_time = self.CIRCULATION_INTERVAL
            self.waiting_queue.append(longest_serving) # 被抢占的房间进入等待队列
            self.serving_queue[index] = new_room
            self.this_thread_cursor.execute('''SELECT bill FROM ROOM WHERE roomId = ?''', (longest_serving.ID,))
            bill = self.this_thread_cursor.fetchone()
            bill = bill[0] if bill else 0.0
            self.send_state_message(longest_serving.ID, "off", bill)
            return True
        else: # 取风速最小的房间进行替换，如果多个风速最小，再取运行时间最长的
            # 找出风速最小的房间
            min_speed = min(room.fan_speed for _, room in replace_rooms)
            min_speed_rooms = [room for room in replace_rooms if room[1].fan_speed == min_speed]
            # 找出运行时间最长的房间
            longest_serving = max(min_speed_rooms, key=lambda x: x[1].running_time)
            index, longest_serving = longest_serving
            longest_serving.state = 'waiting'
            longest_serving.waiting_time = self.CIRCULATION_INTERVAL
            self.waiting_queue.append(longest_serving)  # 被抢占的房间进入等待队列
            self.serving_queue[index] = new_room
            self.this_thread_cursor.execute('''SELECT bill FROM ROOM WHERE roomId = ?''', (longest_serving.ID,))
            bill = self.this_thread_cursor.fetchone()
            bill = bill[0] if bill else 0.0
            self.send_state_message(longest_serving.ID, "off", bill)
            return True

    def search_bill(self, roomId):
        """查询指定房间的账单"""
        self.cursor.execute('''SELECT bill FROM ROOM WHERE roomId = ?''', (roomId,))
        bill = self.cursor.fetchone()
        return bill[0] if bill else 0.0

    async def _send_ws_message(self, ws, message):
        """异步发送WebSocket消息"""
        await ws.send(message)

    def send_state_message(self, roomId, state, bill):
        """发送状态消息到客户端"""
        if roomId in self.room_ws:
            try:
                message = json.dumps({
                    "state": state,
                    "bill": bill
                })
                # 将异步任务提交到事件循环中执行
                asyncio.run_coroutine_threadsafe(
                    self._send_ws_message(self.room_ws[roomId], message),
                    self.loop
                )
            except Exception as e:
                print(f"Error sending message to room {roomId}: {e}")

    def run(self):
        self.database = sqlite3.connect('database.db')
        self.cursor = self.database.cursor()

        last_time = time.time()
        last_bill_time = time.time()

        while True:
            current_time = time.time()
            time_delta = current_time - last_time

            # 更新所有服务中房间的运行时间
            for room in self.serving_queue:
                room.running_time += time_delta
                room.billing_time += time_delta

            # 每0.2秒处理一次计费
            if current_time - last_bill_time >= 0.2:
                for room in self.serving_queue:
                    if room.billing_time > 9.6:
                        room.billing_time -= 9.6
                        if room.fan_speed == 0:
                            self.add_bill(room.ID, self.low_per_minute / 6)
                        elif room.fan_speed == 1:
                            self.add_bill(room.ID, self.medium_per_minute / 6)
                        elif room.fan_speed == 2:
                            self.add_bill(room.ID, self.high_per_minute / 6)
                        self.send_state_message(room.ID, "on", self.search_bill(room.ID))
                last_bill_time = current_time

            self.time_slice_scheduling(time_delta)

            last_time = current_time
            time.sleep(0.1)  # 避免CPU使用率过高

    def time_slice_scheduling(self, time_delta):
        """执行时间片调度"""
        if not self.waiting_queue:
            return

        if len(self.serving_queue) < self.MAX_SERVING:
            # 如果服务队列未满，直接将等待队列中等待服务时长最小的对象加入
            min_remain_waiting = min(self.waiting_queue, key=lambda r: r.waiting_time, default=None)
            if min_remain_waiting:
                min_remain_waiting.state = 'running'
                min_remain_waiting.running_time = 0
                min_remain_waiting.billing_time = 0
                self.serving_queue.append(min_remain_waiting)
                self.waiting_queue.remove(min_remain_waiting)
                self.send_state_message(min_remain_waiting.ID, "on", self.search_bill(min_remain_waiting.ID))

        # 检查是否有等待队列中的房间可以进入服务队列
        for room in self.waiting_queue:
            room.waiting_time -= time_delta
            if room.waiting_time <= 0:
                # 等待时间到，尝试将其加入服务队列。服务队列中服务时长最大的服务对象释放，该房间被放置于等待队列
                max_serving = max(self.serving_queue, key=lambda r: r.running_time, default=None)
                if max_serving:
                    max_serving.state = 'waiting'
                    max_serving.waiting_time = self.CIRCULATION_INTERVAL
                    self.waiting_queue.append(max_serving)
                    self.serving_queue.remove(max_serving)
                    self.send_state_message(max_serving.ID, "off", self.search_bill(max_serving.ID))
                    room.running_time = 0
                    room.billing_time = 0
                    room.state = 'running'
                    self.serving_queue.append(room)
                    self.waiting_queue.remove(room)
                    self.send_state_message(room.ID, "on", self.search_bill(room.ID))

    def findRoomInfo(self, roomId):
        fanSpeed = {0: 'low', 1: 'medium', 2: 'high'}
        for room in self.serving_queue:
            if room.ID == roomId:
                return room.state, fanSpeed[room.fan_speed], room.mode, room.now_temp, room.set_temp
        for room in self.waiting_queue:
            if room.ID == roomId:
                return room.state, fanSpeed[room.fan_speed], room.mode, room.now_temp, room.set_temp
        return 'off', 'off', 'off', '--', '--'

class AirconSchedule:
    def __init__(self, room_ws):
        self.database = sqlite3.connect('database.db')
        self.cursor = self.database.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS USELIST(
                roomId TEXT,
                userId TEXT,
                op_time TEXT,
                operation TEXT,
                set_temp REAL,
                now_temp REAL,
                fan_speed INTEGER,
                mode TEXT
            )
        ''')
        self.database.commit()

        self.scheduler = Scheduler(room_ws)
        self.scheduler_thread = threading.Thread(target=self.scheduler.run) # 单开一个线程执行scheduler.run()
        self.scheduler_thread.start()

    def request(self, data):
        roomId = data['roomId']
        state = data['state']
        speed = data['speed']
        now_temp = data['now_temp']
        set_temp = data['set_temp']
        mode = data['mode']
        new_request = data['new_request']

        if new_request == 1:
            if state == 'on' and self.scheduler.request_on(roomId, speed, set_temp, now_temp, mode):
                self.cursor.execute('''SELECT client_id FROM ROOM WHERE roomId = ?''', (roomId,))
                client_id = self.cursor.fetchone()
                if client_id:
                    client_id = client_id[0]
                    op_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.cursor.execute('''
                        INSERT INTO USELIST (roomId, userId, op_time, operation, set_temp, now_temp, fan_speed, mode)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (roomId, client_id, op_time, state, set_temp, now_temp, speed, mode))
                    self.database.commit()
                self.cursor.execute('''SELECT bill FROM ROOM WHERE roomId = ?''', (roomId,))
                bill = self.cursor.fetchone()
                return {'state': state, 'bill': bill[0] if bill else 0.0}
            else: # 'off' / 'pause' / 'on' but request failed
                if state == 'off' or state == 'pause':
                    self.scheduler.request_off(roomId)
                self.cursor.execute('''SELECT client_id FROM ROOM WHERE roomId = ?''', (roomId,))
                client_id = self.cursor.fetchone()
                if client_id:
                    client_id = client_id[0]
                    op_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.cursor.execute('''
                        INSERT INTO USELIST (roomId, userId, op_time, operation, set_temp, now_temp, fan_speed, mode)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (roomId, client_id, op_time, 'off', set_temp, now_temp, speed, mode))
                    self.database.commit()
                self.cursor.execute('''SELECT bill FROM ROOM WHERE roomId = ?''', (roomId,))
                bill = self.cursor.fetchone()
                return {'state': 'off' if state != 'pause' else 'pause', 'bill': bill[0] if bill else 0.0}

        else:
            self.scheduler.update_request(roomId, set_temp, now_temp, mode)
            self.cursor.execute('''SELECT client_id FROM ROOM WHERE roomId = ?''', (roomId,))
            client_id = self.cursor.fetchone()
            if client_id:
                client_id = client_id[0]
                op_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.cursor.execute('''
                    INSERT INTO USELIST (roomId, userId, op_time, operation, set_temp, now_temp, fan_speed, mode)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (roomId, client_id, op_time, state, set_temp, now_temp, speed, mode))
                self.database.commit()
            self.cursor.execute('''SELECT bill FROM ROOM WHERE roomId = ?''', (roomId,))
            bill = self.cursor.fetchone()
            return {'state': state, 'bill': bill[0] if bill else 0.0}

    def querySchedule(self):
        serving_queue = []
        waiting_queue = [] # str
        for room in self.scheduler.serving_queue:
            serving_queue.append(room.ID)
        for room in self.scheduler.waiting_queue:
            waiting_queue.append(room.ID)
        return {"serving_queue": serving_queue, "waiting_queue": waiting_queue}

    def queryRoomInfo(self, data):
        roomId = data['roomId']
        status, speed, mode, now_temp, set_temp = self.scheduler.findRoomInfo(roomId)
        self.cursor.execute('''SELECT bill FROM ROOM WHERE roomId = ?''', (roomId,))
        bill = self.cursor.fetchone()
        bill = bill[0] if bill else 0.0
        return {
            'roomId': roomId,
            'status': status,
            'speed': speed,
            'mode': mode,
            'now_temp': now_temp,
            'set_temp': set_temp,
            'bill': bill
        }
