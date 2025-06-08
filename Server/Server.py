import asyncio
from sanic import Sanic, response
from sanic.response import json, text
from CentralConditioner import CentralConditioner
from FrontDesk import FrontDesk
import json
from RDR import RDR


# 使用UUID生成真正唯一的名称
app = Sanic(f"soft_air")
clients = {}  # 用于存储连接的客户端

@app.websocket('/ws/room')
async def room_request(request, ws):
    # 新的客户端连接后，添加到客户端集合中
    roomId = request.args.get('roomId', '000')
    print(f"New client connected for room: {roomId}")
    clients[roomId] = ws
    print("Client connected")
    
    try:
        while True:
            data_str = await ws.recv()
            if data_str is None:
                break
            data = json.loads(data_str)
            print(f"Received from client: {data}")
            roomId = data["roomId"]
            #空调开机
            if data["state"] == "on":
                central_conditioner = CentralConditioner()
                if data["speed"] == 0:
                    speed = "low"
                elif data["speed"] == 1:
                    speed = "medium"
                elif data["speed"] == 2:
                    speed = "high"
                result = central_conditioner.set_speed_request(roomId, speed, data["now_temp"], data["set_temp"], data["mode"])
                if result["state"] == "on":
                    # 如果开机成功，记录到数据库
                    pass
                else:
                    await ws.send(json.dumps({"state": result["state"],  "bill": result["bill"]}))
            #空调关机
            elif data["state"] == "off":
                central_conditioner = CentralConditioner()
                result = central_conditioner.delete_server(roomId)
                if result["state"] == "off":
                    # 如果关机成功，记录到数据库
                    await ws.send(json.dumps({"state": result["state"], "bill": result["bill"]}))
                else:
                    await ws.send(json.dumps({"state": result["state"], "bill": result["bill"]}))

    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        # 客户端断开连接时，从集合中移除
        for roomId, socket in clients.items():
            if socket == ws:
                del clients[roomId]
                break
        print("Client disconnected")
# 办理入住
@app.websocket('/ws/checkin')
async def checkin_request(request, ws):
    try:
        while True:
            data_str = await ws.recv()
            if data_str is None:
                break
            data = json.loads(data_str)
            print(f"Received from front desk: {data}")
            # 前台接待处理入住请求
            # 000表示自动分配房间
            front_desk = FrontDesk()
            if data["roomId"] == "000":
                print("Auto allocating room")
                result = front_desk.create_accommodation_order(data["client_name"], data["client_id"])
                print(f"Allocation result: {result}")
                await ws.send(json.dumps({"status": result["status"], "allocate_room": result["allocate_room"]}))
            else:
                # 处理指定房间的入住请求
                result = front_desk.create_accommodation_order(data["client_name"], data["client_id"], data["roomId"])
                await ws.send(json.dumps({"status": result["status"], "allocate_room": result["allocate_room"]}))
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        print("Front desk client disconnected")

# 办理退房
@app.websocket('/ws/checkout')
async def checkout_request(request, ws):
    try:
        while True:
            data_str = await ws.recv()
            if data_str is None:
                break
            data = json.loads(data_str)
            print(f"Received from front desk: {data}")
            # 前台接待处理退房请求
            front_desk = FrontDesk()
            result = front_desk.query_fee_records(data["roomId"])
            await ws.send(json.dumps({"status": "OK", "bill": result["bill"]}))
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        print("Front desk client disconnected")

# 查询账单
@app.websocket('/ws/bill')
async def bill_request(request, ws):
    try:
        while True:
            data_str = await ws.recv()
            if data_str is None:
                break
            data = json.loads(data_str)
            print(f"Received from front desk: {data}")
            # 前台接待处理查询账单请求
            result = RDR.getbill(data["roomId"])
            print(f"Bill result: {result}")
            await ws.send(json.dumps({"bill": result["bill"]}))
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        print("Front desk client disconnected")
        
# 查询详单
@app.websocket('/ws/uselist')
async def use_list_request(request, ws):
    try:
        while True:
            data_str = await ws.recv()
            if data_str is None:
                break
            data = json.loads(data_str)
            print(f"Received from front desk: {data}")
            # 前台接待处理查询详单请求
            result = RDR.getrdr(data["roomId"], data["type"], data["usrId"], data["startTime"], data["endTime"])
            uselist = result["uselist"]
            await ws.send(json.dumps({"uselist": uselist}))
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        print("Front desk client disconnected")

# 前台请求房间状态
@app.websocket('/ws/roominfo')
async def room_info_request(request, ws):
    try:
        while True:
            data_str = await ws.recv()
            if data_str is None:
                break
            data = json.loads(data_str)
            print(f"Received from front desk: {data}")
            # 前台接待处理查询房间状态请求
            front_desk = FrontDesk()
            result = front_desk.get_status()
            await ws.send(json.dumps({"rooms": result["rooms"]}))
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        print("Front desk client disconnected")
        
# 经理查看报表
@app.websocket('/ws/manager')
async def manager_request(request, ws):
    try:
        while True:
            data_str = await ws.recv()
            if data_str is None:
                break
            data = json.loads(data_str)
            print(f"Received from manager: {data}")
            # 经理处理查询报表请求
            result = RDR.get_report(data["startTime"], data["endTime"])
            await ws.send(json.dumps({"content": result}))
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        print("Manager client disconnected")
        
# 管理员查看房间信息
@app.websocket('/ws/query_room_info')
async def query_room_info_request(request, ws):
    try:
        while True:
            data_str = await ws.recv()
            if data_str is None:
                break
            data = json.loads(data_str)
            print(f"Received from admin: {data}")
            # 管理员处理查询房间信息请求
            result = CentralConditioner.get_all_room_info()
            await ws.send(json.dumps(result))
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        print("Admin client disconnected")
        
# 查看当前调度信息
@app.websocket('/ws/scheduling_info')
async def scheduling_info_request(request, ws):
    try:
        while True:
            data_str = await ws.recv()
            if data_str is None:
                break
            data = json.loads(data_str)
            print(f"Received from admin: {data}")
            # 管理员处理查询当前调度信息请求
            result = RDR.get_scheduling_info()
            await ws.send(json.dumps({"serving_queue": result["serving_queue"], "waiting_queue": result["waiting_queue"]}))
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        print("Admin client disconnected")

if __name__ == '__main__':
    # 使用 WebSocketProtocol 协议运行 Sanic
    app.run(host="0.0.0.0", port=10043, auto_reload=False)
