import sys
from typing import cast
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLCDNumber, QLabel, QSizePolicy, QGraphicsColorizeEffect,
    QMessageBox, QInputDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QSize, pyqtBoundSignal, QTimer, QEventLoop

from client import AirconClient, RequestMessage
from room import Room

class ClientGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(" SoftAir Client ")
        self.setWindowIcon(QIcon("./resource/wind.ico"))
        self.setMinimumSize(1100, 550)
        self.setMaximumSize(1200, 650)

        # 房间
        self.room = Room()
        while True:
            room_number, ok = QInputDialog.getText(self, "输入房间号", "请输入当前房间号（例如：888）：")
            if ok and room_number.strip():
                self.room.set_room_id(room_number.strip())
                break
            else:
                QMessageBox.warning(self, "输入错误", "房间号不能为空，请重新输入。")
        while True:
            temp_str, ok = QInputDialog.getText(self, "设置初始温度", "请输入房间初始温度（例如：23.5）：")
            if ok:
                try:
                    initial_temperature = float(temp_str)
                    if initial_temperature < 10 or initial_temperature > 35:
                        QMessageBox.critical(self, "温度范围错误", "请输入10到35之间的温度。")
                        continue
                    self.room.init_current_temp(initial_temperature)
                    break
                except ValueError:
                    QMessageBox.critical(self, "格式错误", "请输入有效的浮点数作为温度。")
        self.current_temp_timer = QTimer(self)
        cast(pyqtBoundSignal, self.current_temp_timer.timeout).connect(self.refresh_current_temp)
        self.current_temp_timer.start(1000) # 每秒刷新一次当前温度

        # 系统状态
        self.power_on = False
        self.sleep_mode = False # 房间的温度达到目标值以后，客户端自动发送停止送风请求给服务端。此时进入睡眠模式
        self.mode = 'cool'
        self.current_temp = self.room.get_current_temp()
        self.set_temp = 25.0
        self.fan_speeds_show = ['|  ', '|| ', '|||']
        self.fan_index = 1 # 缺省风速为中速
        self.now_cost = 0.0 # 当前费用

        self.request_list = [] # 请求列表
        self.send_timer = QTimer(self) # 发送请求计时器
        cast(pyqtBoundSignal, self.send_timer.timeout).connect(self._send_request)

        # LCD温度显示占位
        self.lcd_set = None
        self.lcd_current = None

        # Central widget
        central = QWidget(self)
        self.setCentralWidget(central)

        # Base layout
        base_layout = QHBoxLayout(central)
        base_layout.addStretch(1)
        base_layout.addWidget(self._create_button_area(), stretch=2)
        base_layout.addStretch(2)
        base_layout.addWidget(self._create_status_area(), stretch=10)
        base_layout.addStretch(1)

        # 前后端连接
        self.client = AirconClient(self.room.get_room_id(), self.room.set_cost, self.receive_server_schedule)
        self.client.server_connect()

        loop = QEventLoop()
        QTimer.singleShot(400, loop.quit)  # 等待连接400ms
        loop.exec_() # 暂停400ms同时不打断Qt事件

        while True:
            if self.client.connected():
                self.connect_color_effect.setColor(Qt.green)
                break
            else:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("连接失败")
                msg_box.setText("无法连接到服务器，请检查网络设置。")
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
                retry_button = msg_box.button(QMessageBox.Retry)
                retry_button.setText("重试")
                cancel_button = msg_box.button(QMessageBox.Cancel)
                cancel_button.setText("取消")
                ret = msg_box.exec_()
                if ret == QMessageBox.Retry:
                    self.client.server_connect()
                elif ret == QMessageBox.Cancel:
                    QMessageBox.information(self, "提示", "程序将退出。")
                    sys.exit(0)

    def _create_button_area(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)

        # 开关机按钮
        self.btn_power = QPushButton()
        self.btn_power.setIcon(QIcon("./resource/toggle-off.svg"))
        self.btn_power.setIconSize(QSize(48, 48))
        self.btn_power.setCheckable(True)
        cast(pyqtBoundSignal, self.btn_power.clicked).connect(self.toggle_power) # 显式转换为pyqtBoundSignal，以避免警告
        layout.addWidget(self.btn_power)

        # 温度加按钮
        self.btn_plus = QPushButton()
        self.btn_plus.setIcon(QIcon("./resource/plus.svg"))
        self.btn_plus.setIconSize(QSize(48, 48))
        cast(pyqtBoundSignal, self.btn_plus.clicked).connect(self.increase_set_temp)
        layout.addWidget(self.btn_plus)

        # 温度减按钮
        self.btn_minus = QPushButton()
        self.btn_minus.setIcon(QIcon("./resource/minus.svg"))
        self.btn_minus.setIconSize(QSize(48, 48))
        cast(pyqtBoundSignal, self.btn_minus.clicked).connect(self.decrease_set_temp)
        layout.addWidget(self.btn_minus)

        # 模式切换按钮
        self.btn_mode = QPushButton()
        self._update_mode_icon()
        cast(pyqtBoundSignal, self.btn_mode.clicked).connect(self.switch_mode)
        layout.addWidget(self.btn_mode)

        # 风速切换按钮
        self.btn_fan = QPushButton()
        self.btn_fan.setIcon(QIcon("./resource/fan.svg"))
        self.btn_fan.setIconSize(QSize(48, 48))
        cast(pyqtBoundSignal, self.btn_fan.clicked).connect(self.cycle_fan)
        layout.addWidget(self.btn_fan)

        return container

    def _create_status_area(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(30)

        layout.addStretch(1)

        # 上方：两个LCD并排显示
        top_layout = QHBoxLayout()
        # 设定温度显示
        self.lcd_set = QLCDNumber()
        self.lcd_set.setDigitCount(4)
        self.lcd_set.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lcd_set.setFixedSize(300, 200)
        self.lcd_set.display(f'{self.set_temp:.1f}')
        set_widget = self._labeled_widget("设定温度", self.lcd_set)
        top_layout.addWidget(set_widget)

        # 当前温度显示
        self.lcd_current = QLCDNumber()
        self.lcd_current.setDigitCount(4)
        self.lcd_current.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lcd_current.setFixedSize(300, 200)
        self.lcd_current.display(f'{self.current_temp:.1f}')
        curr_widget = self._labeled_widget("室内温度", self.lcd_current)
        top_layout.addWidget(curr_widget)

        layout.addLayout(top_layout)

        # 下方：连接状态显示和风速文字显示
        below_layout = QHBoxLayout()
        # 连接状态显示
        self.signal_lbl = QLabel("连接状态")
        below_layout.addWidget(self.signal_lbl, stretch=1)
        
        self.signal_svg = QSvgWidget("./resource/wifi.svg")
        self.signal_svg.setFixedSize(24, 24)
        self.connect_color_effect = QGraphicsColorizeEffect(self.signal_svg)
        self.connect_color_effect.setStrength(1.0)  # 颜色覆盖强度
        self.signal_svg.setGraphicsEffect(self.connect_color_effect)
        self.connect_color_effect.setColor(Qt.red)  # 设置颜色
        below_layout.addWidget(self.signal_svg, stretch=1)
        below_layout.addStretch(5)

        # 风速文字显示
        self.lbl_fan_speed = QLabel(f"风速: {self.fan_speeds_show[self.fan_index]} 停止送风")
        self.lbl_fan_speed.setAlignment(Qt.AlignCenter)
        below_layout.addWidget(self.lbl_fan_speed, stretch=1)
        below_layout.addStretch(5)

        # 当前费用显示
        self.lbl_cost = QLabel(f"当前费用: {self.now_cost:.2f} 元")
        self.lbl_cost.setAlignment(Qt.AlignCenter)
        below_layout.addWidget(self.lbl_cost, stretch=1)
        below_layout.addStretch(5)

        layout.addLayout(below_layout)

        layout.addStretch(1)
        return container

    @staticmethod
    def _labeled_widget(text, widget):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)
        layout.addWidget(widget)
        return container

    def toggle_power(self):
        self.power_on = not self.power_on
        self.sleep_mode = False
        self.request_service(type=1)
        icon = "toggle-on.svg" if self.power_on else "toggle-off.svg"
        self.btn_power.setIcon(QIcon(f"./resource/{icon}"))

        if self.power_on and (not self.sleep_mode):
            self.lbl_fan_speed.setText(f"风速: {self.fan_speeds_show[self.fan_index]} 正在送风")
            self.room.set_wind(self.set_temp, self.fan_index, self.mode)
        else:
            self.lbl_fan_speed.setText(f"风速: {self.fan_speeds_show[self.fan_index]} 停止送风")
            self.room.stop_wind()

    def switch_mode(self):
        self.mode = 'heat' if self.mode == 'cool' else 'cool'
        self._update_mode_icon()
        self.set_temp = 25.0
        self.lcd_set.display(f'{self.set_temp:.1f}')
        self.request_service(type=1)
        self.room.set_wind(self.set_temp, self.fan_index, self.mode)

    def _update_mode_icon(self):
        file = "snowflake.svg" if self.mode == 'cool' else "sun.svg"
        self.btn_mode.setIcon(QIcon(f"./resource/{file}"))
        self.btn_mode.setIconSize(QSize(48, 48))

    def increase_set_temp(self):
        if self.mode == 'cool' and self.set_temp < 25:
            self.set_temp += 1
            self.lcd_set.display(f'{self.set_temp:.1f}')
            self.sleep_mode = False
            self.lbl_fan_speed.setText(f"风速: {self.fan_speeds_show[self.fan_index]} 正在送风")
            self.request_service(type=0)
            self.room.set_wind(self.set_temp, self.fan_index, self.mode)
        elif self.mode == 'heat' and self.set_temp < 30:
            self.set_temp += 1
            self.lcd_set.display(f'{self.set_temp:.1f}')
            self.sleep_mode = False
            self.lbl_fan_speed.setText(f"风速: {self.fan_speeds_show[self.fan_index]} 正在送风")
            self.request_service(type=0)
            self.room.set_wind(self.set_temp, self.fan_index, self.mode)

    def decrease_set_temp(self):
        if self.mode == 'cool' and self.set_temp > 18:
            self.set_temp -= 1
            self.lcd_set.display(f'{self.set_temp:.1f}')
            self.sleep_mode = False
            self.lbl_fan_speed.setText(f"风速: {self.fan_speeds_show[self.fan_index]} 正在送风")
            self.request_service(type=0)
            self.room.set_wind(self.set_temp, self.fan_index, self.mode)
        elif self.mode == 'heat' and self.set_temp > 25:
            self.set_temp -= 1
            self.lcd_set.display(f'{self.set_temp:.1f}')
            self.sleep_mode = False
            self.lbl_fan_speed.setText(f"风速: {self.fan_speeds_show[self.fan_index]} 正在送风")
            self.request_service(type=0)
            self.room.set_wind(self.set_temp, self.fan_index, self.mode)

    def cycle_fan(self):
        self.fan_index = (self.fan_index + 1) % len(self.fan_speeds_show)
        self.request_service(type=2)
        self.room.set_wind(self.set_temp, self.fan_index, self.mode)
        if self.power_on and (not self.sleep_mode):
            self.lbl_fan_speed.setText(f"风速: {self.fan_speeds_show[self.fan_index]} 正在送风")
        else:
            self.lbl_fan_speed.setText(f"风速: {self.fan_speeds_show[self.fan_index]} 停止送风")

    def request_service(self, type = 0):
        self.request_list.append(RequestMessage(
            request_on_off=self.power_on and (not self.sleep_mode),
            request_temp=self.set_temp,
            request_mode=self.mode,
            request_fan=self.fan_index,
            request_type=type
        ))
        # 计时：刷新计时器为1s，1s到后只发送最后1次的指令参数
        if self.send_timer.isActive():
            self.send_timer.stop()
        self.send_timer.start(1000)

    def _send_request(self):
        if self.request_list:
            msg = self.request_list.pop()
            self.client.send_message(msg)
            self.request_list.clear() # 可能会有多次的请求，中间的请求会被丢弃
        self.send_timer.stop()

    def receive_server_schedule(self, schedule_on_off: bool):
        if self.power_on == schedule_on_off:
            return # 如果当前状态和服务器的调度状态相同，则不需要更新
        self.power_on = schedule_on_off
        if self.power_on:
            self.btn_power.setIcon(QIcon("./resource/toggle-on.svg"))
            self.btn_power.setChecked(True)
            self.lbl_fan_speed.setText(f"风速: {self.fan_speeds_show[self.fan_index]} 正在送风")
            self.room.set_wind(self.set_temp, self.fan_index, self.mode)
        else:
            self.btn_power.setIcon(QIcon("./resource/toggle-off.svg"))
            self.btn_power.setChecked(False)
            self.lbl_fan_speed.setText(f"风速: {self.fan_speeds_show[self.fan_index]} 停止送风")
            self.room.stop_wind()

    def refresh_current_temp(self):
        self.current_temp = self.room.get_current_temp()
        self.lcd_current.display(f'{self.current_temp:.1f}')
        self.now_cost = self.room.get_cost()
        self.lbl_cost.setText(f"当前费用: {self.now_cost:.2f} 元")
        if (self.mode=='cool' and self.current_temp<=self.set_temp) and self.power_on and (not self.sleep_mode):
            self.sleep_mode = True
            self.room.stop_wind()
            self.lbl_fan_speed.setText(f"风速: {self.fan_speeds_show[self.fan_index]} 停止送风")
            self.client.send_message(RequestMessage(
                request_on_off=False,
                request_temp=self.set_temp,
                request_mode=self.mode,
                request_fan=self.fan_index,
                request_type=1
            ))
            if self.send_timer.isActive():
                self.send_timer.stop()
                self.request_list.clear()
        elif (self.mode=='heat' and self.current_temp>=self.set_temp) and self.power_on and (not self.sleep_mode):
            self.sleep_mode = True
            self.room.stop_wind()
            self.lbl_fan_speed.setText(f"风速: {self.fan_speeds_show[self.fan_index]} 停止送风")
            self.client.send_message(RequestMessage(
                request_on_off=False,
                request_temp=self.set_temp,
                request_mode=self.mode,
                request_fan=self.fan_index,
                request_type=1
            ))
            if self.send_timer.isActive():
                self.send_timer.stop()
                self.request_list.clear()

        if abs(self.current_temp - self.set_temp) > 1 and self.sleep_mode and self.power_on:
            if (self.mode=='heat' and self.current_temp>=self.set_temp) or (self.mode=='cool' and self.current_temp<=self.set_temp):
                return
            self.sleep_mode = False
            self.lbl_fan_speed.setText(f"风速: {self.fan_speeds_show[self.fan_index]} 正在送风")
            self.request_service(type=1)
            self.room.set_wind(self.set_temp, self.fan_index, self.mode)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ClientGUI()
    window.show()
    sys.exit(app.exec_())