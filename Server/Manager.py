import sqlite3

class Manager:
    def __init__(self):
        self.database = sqlite3.connect('database.db')
        self.cursor = self.database.cursor()

    def show(self, data):
        start_time = data.get('start_time')
        end_time = data.get('end_time') # YYYY-MM-DD HH:MM:SS

        if start_time and end_time:
            self.cursor.execute('''
                SELECT * FROM USELIST WHERE op_time >= ? AND op_time <= ?
            ''', (start_time, end_time))
        else:
            self.cursor.execute('SELECT * FROM USELIST')
        all_use = self.cursor.fetchall()
        all_use_str = ""
        fan_speed = {0: 'Low', 1: 'Medium', 2: 'High'}
        for use in all_use:
            all_use_str += f"""Room {use[0]}, User {use[1]}, Time {use[2]} : {use[3]}, set {use[4]}℃ at {use[5]}℃, 
            using fan speed {fan_speed[use[6]]}, {use[7]} mode\n"""
        return {'content': all_use_str}

