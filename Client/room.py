from typing import cast
from PyQt5.QtCore import pyqtBoundSignal, QTimer

class Room:
    def __init__(self):
        self.room_id = '000'
        self.init_temp = 25.0
        self.current_temp = 25.0
        self.running = False
        self.set_temp = 25.0
        self.fan_speed = 0
        self.mode = None
        self.now_cost_times_six = 0 # 当前费用的六倍，由于3不能被整除

        self.refresh_temp_timer = QTimer()
        cast(pyqtBoundSignal, self.refresh_temp_timer.timeout).connect(self.change_temp)
        self.refresh_temp_timer.start(60000)

        self.calculate_cost_timer = QTimer()
        cast(pyqtBoundSignal, self.calculate_cost_timer.timeout).connect(self.calculate_cost)
        self.calculate_cost_timer.start(60000)

    def set_room_id(self, room_id):
        self.room_id = room_id
    def get_room_id(self):
        return self.room_id

    def init_current_temp(self, temp):
        self.init_temp = temp
        self.current_temp = temp
    def get_current_temp(self):
        return self.current_temp

    def set_cost(self, cost):
        self.now_cost_times_six = cost * 6
    def get_cost(self):
        return self.now_cost_times_six / 6

    def set_wind(self, temp, wind, mode):
        if not self.running:
            self.set_temp = temp
            self.fan_speed = wind
            self.mode = mode
            self.running = True
            self.refresh_temp_timer.stop()
            self.refresh_temp_timer.start(60000)
            self.calculate_cost_timer.stop()
            self.calculate_cost_timer.start(60000)
        else:
            self.set_temp = temp
            self.fan_speed = wind
            self.mode = mode

    def stop_wind(self):
        self.running = False
        self.set_temp = 25.0
        self.fan_speed = 0
        self.refresh_temp_timer.stop()
        self.refresh_temp_timer.start(60000)
        self.calculate_cost_timer.stop()
        self.calculate_cost_timer.start(60000)

    def change_temp(self):
        if self.running:
            # 中风模式下每分钟变化0.5度
            # 高风模式每分钟变化率提高20%，低风模式每分钟变化率减小20%
            if self.mode == 'cool':
                if self.fan_speed == 0:
                    self.current_temp -= 0.4
                elif self.fan_speed == 1:
                    self.current_temp -= 0.5
                elif self.fan_speed == 2:
                    self.current_temp -= 0.6
            elif self.mode == 'heat':
                if self.fan_speed == 0:
                    self.current_temp += 0.4
                elif self.fan_speed == 1:
                    self.current_temp += 0.5
                elif self.fan_speed == 2:
                    self.current_temp += 0.6

        else:
            # 关机状态下，每分钟变化0.5度，直到变化到初始温度为止
            if abs(self.current_temp - self.init_temp) < 0.5:
                self.current_temp = self.init_temp # 如果变化0.5以内即到初始温度，则直接设置为初始温度

            if self.current_temp > self.init_temp:
                self.current_temp -= 0.5
            elif self.current_temp < self.init_temp:
                self.current_temp += 0.5

    def calculate_cost(self):
        if self.running:
            if self.fan_speed == 0: # 低风模式，每3分钟消耗1单位电，即每分钟消耗1/3单位电 => 每分钟消耗2个六倍计数
                self.now_cost_times_six += 2
            elif self.fan_speed == 1: # 中风模式，每2分钟消耗1单位电，即每分钟消耗1/2单位电 => 每分钟消耗3个六倍计数
                self.now_cost_times_six += 3
            elif self.fan_speed == 2: # 高风模式，每1分钟消耗1单位电
                self.now_cost_times_six += 6