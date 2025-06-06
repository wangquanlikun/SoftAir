class RequestMessage:
    def __init__(self,request_on_off ,request_temp, request_mode, request_fan, request_type, now_room_temp):
        self.on_off = request_on_off
        self.temp = request_temp
        self.room_temp = now_room_temp
        self.mode = request_mode
        self.fan = request_fan
        self.type = request_type
        # type = 0 : 仅改变了温度（不发送新请求）
        # type = 1 : 开启/关闭空调
        # type = 2 : 改变了风速

from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtCore import QUrl
import json

class AirconClient:
    def __init__(self, room_id: str, change_bill, change_state, host='127.0.0.1', port=10043):
        self.host = host
        self.port = port
        self.room_id = room_id
        self.status = False
        self.ws = QWebSocket()
        self.change_bill = change_bill
        self.change_state = change_state

    def server_connect(self):
        if self.status:
            print("WebSocket 已经连接，无需重新连接。")
            return
        self.ws.error.connect(self.on_error)
        self.ws.connected.connect(self.on_connected)
        self.ws.textMessageReceived.connect(self.on_message)
        self.ws.disconnected.connect(self.on_disconnected)
        server_url = f"ws://{self.host}:{self.port}/ws/room"
        print(f"正在尝试连接到 {server_url} ...")
        self.ws.open(QUrl(server_url))

    def connected(self):
        return self.status

    def on_connected(self):
        print(f"已连接到服务器 {self.host}:{self.port}")
        self.status = True

    def on_disconnected(self):
        print(f"与服务器 {self.host}:{self.port} 的连接已断开")
        self.status = False

    def on_error(self, error):
        print(f"WebSocket 错误: {error}")
        self.status = False

    def on_message(self, message: str):
        print(f"Received message: {message}")
        json_msg = json.loads(message)
        state = True if json_msg['state'] == 'on' else False
        bill = json_msg['bill']
        self.change_state(state)
        self.change_bill(bill)

    def send_message(self, msg: RequestMessage):
        print(f'Message: {msg.on_off}, {msg.temp}, {msg.mode}, {msg.fan}, {msg.type}')
        if self.ws is not None and self.ws.isValid():
            if msg.type == 1 or msg.type == 2:
                json_msg = {
                    "roomId": self.room_id,
                    "state": "on" if msg.on_off else "off",
                    "speed": msg.fan,
                    "now_temp": msg.room_temp,
                    "set_temp": msg.temp,
                    "mode": msg.mode,
                    "new_request": 1
                }
                self.ws.sendTextMessage(json.dumps(json_msg))
            elif msg.type == 0:
                json_msg = {
                    "roomId": self.room_id,
                    "state": "on" if msg.on_off else "off",
                    "speed": msg.fan,
                    "now_temp": msg.room_temp,
                    "set_temp": msg.temp,
                    "mode": msg.mode,
                    "new_request": 0
                }
                self.ws.sendTextMessage(json.dumps(json_msg))
        else:
            print("WebSocket is not connected.")