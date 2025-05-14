class RequestMessage:
    def __init__(self,request_on_off ,request_temp, request_mode, request_fan):
        self.on_off = request_on_off
        self.temp = request_temp
        self.mode = request_mode
        self.fan = request_fan

class AirconClient:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port

    def connect(self):
        pass

    def send_message(self, msg: RequestMessage):
        print(f'Send message: {msg.on_off}, {msg.temp}, {msg.mode}, {msg.fan}')
        pass # TODO: 具体等待实现