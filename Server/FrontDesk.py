import sqlite3

class FrontDesk:
    def __init__(self):
        self.database = sqlite3.connect('database.db')
        self.cursor = self.database.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ROOM (
                roomId TEXT PRIMARY KEY,
                status TEXT,
                client_name TEXT,
                client_id TEXT,
                bill REAL DEFAULT 0.0
            )
        ''')
        self.database.commit()

        # 初始化房间状态
        for roomId in ['101', '102', '103', '104', '201', '202', '203', '204']:
            self.cursor.execute('''
                INSERT OR IGNORE INTO ROOM (roomId, status) VALUES (?, 'free')
            ''', (roomId,))
        self.database.commit()

    def checkin(self, data):
        roomId = data['roomId']
        client_name = data['client_name']
        client_id = data['client_id']
        if roomId == '000': # 系统自动分配空房
            self.cursor.execute("SELECT * FROM ROOM WHERE status = 'free' LIMIT 1")
            room = self.cursor.fetchone()
            if room:
                roomId = room[0]
                self.cursor.execute('''
                    UPDATE ROOM SET status = ?, client_name = ?, client_id = ?
                    WHERE roomId = ?
                ''', ('busy', client_name, client_id, roomId))
                self.database.commit()
                return {'status': 'OK', 'allocate_room': roomId }
            return {'status': 'ERR', 'allocate_room': '000'}
        else:
            self.cursor.execute("SELECT status FROM ROOM WHERE roomId = ?", (roomId,))
            room_status = self.cursor.fetchone()
            if room_status and room_status[0] == 'free':
                self.cursor.execute('''
                    UPDATE ROOM SET status = ?, client_name = ?, client_id = ?
                    WHERE roomId = ?
                ''', ('busy', client_name, client_id, roomId))
                self.database.commit()
                return {'status': 'OK', 'allocate_room': roomId }
            else:
                return {'status': 'ERR', 'allocate_room': '000'}

    def checkout(self, data):
        roomId = data['roomId']
        self.cursor.execute("SELECT status FROM ROOM WHERE roomId = ?", (roomId,))
        room_status = self.cursor.fetchone()
        if room_status and room_status[0] == 'busy':
            self.cursor.execute('''SELECT bill FROM ROOM WHERE roomId = ?''', (roomId,))
            bill = self.cursor.fetchone()[0]

            self.cursor.execute('''
            UPDATE ROOM SET status = 'free', client_name = NULL, client_id = NULL, bill = 0.0
                WHERE roomId = ?
            ''', (roomId,))
            self.database.commit()
            return {'status': 'OK', 'bill': bill}
        else:
            return {'status': 'ERR'}

    def bill(self, data):
        roomId = data['roomId']
        self.cursor.execute("SELECT bill FROM ROOM WHERE roomId = ?", (roomId,))
        bill = self.cursor.fetchone()
        if bill:
            return {'bill': bill[0]}
        else:
            return {'bill': 0.0}

    def userList(self, data):
        uselist = ""
        roomId = data['roomId']
        type = data['type']
        if type == 'usr':
            usrId = data['usrId']
            self.cursor.execute('''
                SELECT * FROM USELIST WHERE userId = ? AND roomId = ?
            ''', (usrId, roomId))
            use_list = self.cursor.fetchall()
            fan_speed = {0: '低', 1: '中', 2: '高'}
            status = {'on': '开机', 'off': '关机', 'cool': '制冷', 'heat': '制热', 'pause': '暂停'}
            for use in use_list:
                uselist += f"- 房间号 {use[0]}, 住户ID {use[1]}\n"
                uselist += f"\t时间 {use[2]} : {status[use[3]]}, 设定温度 {use[4]}℃, 房间温度 {round(float(use[5]), 1)}℃\n"
                uselist += f"\t风速 {fan_speed[use[6]]}, {status[use[7]]} 模式, 总花费 {use[8]} 元\n"

        elif type == 'room':
            start_time = data['start_time']
            end_time = data['end_time']
            if start_time and end_time:
                self.cursor.execute('''
                    SELECT * FROM USELIST WHERE roomId = ? AND op_time >= ? AND op_time <= ?
                ''', (roomId, start_time, end_time))
            else:
                self.cursor.execute('SELECT * FROM USELIST WHERE roomId = ?', (roomId,))
            use_list = self.cursor.fetchall()
            fan_speed = {0: '低', 1: '中', 2: '高'}
            status = {'on': '开机', 'off': '关机', 'cool': '制冷', 'heat': '制热', 'pause': '暂停'}
            for use in use_list:
                uselist += f"- 房间号 {use[0]}, 住户ID {use[1]}, \n"
                uselist += f"\t时间 {use[2]} : {status[use[3]]}, 设定温度 {use[4]}℃, 房间温度 {round(float(use[5]), 1)}℃\n"
                uselist += f"\t风速 {fan_speed[use[6]]}, {status[use[7]]} 模式, 总花费 {use[8]} 元\n"

        return {'uselist': uselist}

    def roomInfo(self): # 各个房间状态
        self.cursor.execute("SELECT * FROM ROOM")
        rooms = self.cursor.fetchall()
        room_list = []
        for room in rooms:
            room_info = {
                'roomId': room[0],
                'status': room[1]
            }
            room_list.append(room_info)
        return {'rooms': room_list}