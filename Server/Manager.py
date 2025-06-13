import sqlite3

class Manager:
    def __init__(self):
        self.database = sqlite3.connect('database.db')
        self.cursor = self.database.cursor()
        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS EARNING(
                roomId TEXT,
                op_time TEXT,
                money REAL
            )
            '''
        )
        self.database.commit()

    def show(self, data):
        start_time = data.get('start_time')
        end_time = data.get('end_time') # YYYY-MM-DD HH:MM:SS

        if start_time and end_time:
            self.cursor.execute('''
                SELECT * FROM EARNING WHERE op_time >= ? AND op_time <= ?
            ''', (start_time, end_time))
        else:
            self.cursor.execute('SELECT * FROM EARNING')
        all_earn = self.cursor.fetchall()
        all_earn_str = ""
        for earn in all_earn:
            all_earn_str += f"-- 房间号 {earn[0]} 在时间点 {earn[1]} 新增营收 {earn[2]} 元\n"
        room_earn = {}
        for earn in all_earn:
            if earn[0] not in room_earn:
                room_earn[earn[0]] = 0
            room_earn[earn[0]] += earn[2]
        room_earn_str = f"从 {start_time} 到 {end_time}, 酒店空调营收情况为：\n" if start_time and end_time \
            else "酒店空调营收情况为：\n"
        for room, earn in room_earn.items():
            room_earn_str += f"- 房间号 {room} 总营收： {earn} 元\n"
        return {'content': room_earn_str + "\n具体营收情况：\n" + all_earn_str}

