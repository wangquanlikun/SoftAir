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
        self.now_cost = 0.0

        self.TIME_SPEED = 6 # 时间流速倍率

        self.refresh_temp_timer = QTimer()
        cast(pyqtBoundSignal, self.refresh_temp_timer.timeout).connect(self.change_temp)
        self.refresh_temp_timer.start(int(6000 / self.TIME_SPEED))

        self.calculate_cost_timer = QTimer()
        cast(pyqtBoundSignal, self.calculate_cost_timer.timeout).connect(self.calculate_cost)
        self.calculate_cost_timer.start(int(6000 / self.TIME_SPEED))

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
        self.now_cost = cost
    def get_cost(self):
        return self.now_cost

    def set_wind(self, temp, wind, mode):
        if not self.running:
            self.set_temp = temp
            self.fan_speed = wind
            self.mode = mode
            self.running = True
            self.refresh_temp_timer.stop()
            self.refresh_temp_timer.start(int(6000 / self.TIME_SPEED))
            self.calculate_cost_timer.stop()
            self.calculate_cost_timer.start(int(6000 / self.TIME_SPEED))
        else:
            self.set_temp = temp
            self.fan_speed = wind
            self.mode = mode

    def stop_wind(self):
        self.running = False
        self.set_temp = 25.0
        self.fan_speed = 0
        self.refresh_temp_timer.stop()
        self.refresh_temp_timer.start(int(6000 / self.TIME_SPEED))
        self.calculate_cost_timer.stop()
        self.calculate_cost_timer.start(int(6000 / self.TIME_SPEED))

    def change_temp(self):
        if self.running:
            # 中风模式下每分钟变化0.5度
            # 高风模式每分钟变化率提高20%，低风模式每分钟变化率减小20%
            if self.mode == 'cool':
                if self.fan_speed == 0:
                    self.current_temp -= 0.04
                elif self.fan_speed == 1:
                    self.current_temp -= 0.05
                elif self.fan_speed == 2:
                    self.current_temp -= 0.06
            elif self.mode == 'heat':
                if self.fan_speed == 0:
                    self.current_temp += 0.04
                elif self.fan_speed == 1:
                    self.current_temp += 0.05
                elif self.fan_speed == 2:
                    self.current_temp += 0.06

        else:
            # 关机状态下，每分钟变化0.5度，直到变化到初始温度为止
            if abs(self.current_temp - self.init_temp) < 0.05:
                self.current_temp = self.init_temp # 如果变化0.5以内即到初始温度，则直接设置为初始温度

            if self.current_temp > self.init_temp:
                self.current_temp -= 0.05
            elif self.current_temp < self.init_temp:
                self.current_temp += 0.05

    def calculate_cost(self):
        if self.running:
            if self.fan_speed == 0: # 低风模式，每3分钟消耗1单位电，即每分钟消耗1/3单位电
                self.now_cost += 2 / 60
            elif self.fan_speed == 1: # 中风模式，每2分钟消耗1单位电，即每分钟消耗1/2单位电
                self.now_cost += 3 / 60
            elif self.fan_speed == 2: # 高风模式，每1分钟消耗1单位电
                self.now_cost += 6 / 60