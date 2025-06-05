class RequestMessage:
    def __init__(self,request_on_off ,request_temp, request_mode, request_fan):
        self.on_off = request_on_off
        self.temp = request_temp
        self.mode = request_mode
        self.fan = request_fan

from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtCore import QUrl

class AirconClient:
    def __init__(self, room_id: str, host='127.0.0.1', port=10043):
        self.host = host
        self.port = port
        self.room_id = room_id
        self.status = False
        self.ws = QWebSocket()

    def server_connect(self):
        if self.status:
            print("WebSocket 已经连接，无需重新连接。")
            return
        self.ws.error.connect(self.on_error)
        self.ws.connected.connect(self.on_connected)
        self.ws.textMessageReceived.connect(self.on_message)
        self.ws.disconnected.connect(self.on_disconnected)
        server_url = f"ws://{self.host}:{self.port}/ws"
        print(f"正在尝试连接到 {server_url} ...")
        self.ws.open(QUrl(server_url))

    def connected(self):
        return self.status

    def on_connected(self):
        print(f"已连接到服务器 {self.host}:{self.port}")
        self.ws.sendTextMessage(self.room_id)
        self.status = True

    def on_disconnected(self):
        print(f"与服务器 {self.host}:{self.port} 的连接已断开")
        self.status = False

    def on_error(self, error):
        print(f"WebSocket 错误: {error}")
        self.status = False

    def on_message(self, message: str):
        print(f"Received message: {message}")
        pass # TODO: 具体等待实现

    def send_message(self, msg: RequestMessage, type = 0):
        print(f'Send message: {msg.on_off}, {msg.temp}, {msg.mode}, {msg.fan}')
        if self.ws is not None and self.ws.isValid():
            self.ws.sendTextMessage(f"{msg.on_off},{msg.temp},{msg.mode},{msg.fan},{type}")
            pass # TODO: 具体等待实现
        else:
            print("WebSocket is not connected.")