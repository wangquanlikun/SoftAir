from sanic import Sanic
import json

app = Sanic("SoftAirServer")
room_ws = {}

import FrontDesk as fd
frontDesk = fd.FrontDesk()

import AirconSchedule as acs
airconSchedule = acs.AirconSchedule(room_ws)

import Manager as mg
manager = mg.Manager()

@app.websocket('/ws/room')
async def room_request(request, ws):
    roomId = request.args.get('roomId', "000")
    room_ws[roomId] = ws
    print(f"Client connected to room: {roomId}")
    try:
        while True:
            msg = await ws.recv()
            if msg is None:
                break
            data = json.loads(msg)
            ret = airconSchedule.request(data)
            await ws.send(json.dumps(ret))
    except Exception as e:
        print(f"Connection error in room {roomId}: {e}")
    finally:
        if roomId in room_ws:
            del room_ws[roomId]
        airconSchedule.request({'roomId': roomId, 'state': "off", 'speed': 0, 'mode': "off", 'now_temp': 0, 'set_temp': 0, 'new_request': 1})
        print(f"Client disconnected from room: {roomId}")

@app.websocket('/ws/checkin')
async def checkin_request(_, ws):
    try:
        while True:
            msg = await ws.recv()
            if msg is None:
                break
            data = json.loads(msg)
            ret = frontDesk.checkin(data)
            await ws.send(json.dumps(ret))
    except Exception as e:
        print(f"Connection error in checkin: {e}")
    finally:
        print("Client disconnected from checkin")

@app.websocket('/ws/checkout')
async def checkout_request(_, ws):
    try:
        while True:
            msg = await ws.recv()
            if msg is None:
                break
            data = json.loads(msg)
            ret = frontDesk.checkout(data)
            await ws.send(json.dumps(ret))
    except Exception as e:
        print(f"Connection error in checkout: {e}")
    finally:
        print("Client disconnected from checkout")

@app.websocket('/ws/bill')
async def bill_request(_, ws):
    try:
        while True:
            msg = await ws.recv()
            if msg is None:
                break
            data = json.loads(msg)
            ret = frontDesk.bill(data)
            await ws.send(json.dumps(ret))
    except Exception as e:
        print(f"Connection error in bill: {e}")
    finally:
        print("Client disconnected from bill")

@app.websocket('/ws/uselist')
async def uselist_request(_, ws):
    try:
        while True:
            msg = await ws.recv()
            if msg is None:
                break
            data = json.loads(msg)
            ret = frontDesk.userList(data)
            await ws.send(json.dumps(ret))
    except Exception as e:
        print(f"Connection error in user list: {e}")
    finally:
        print("Client disconnected from user list")

@app.websocket('/ws/roominfo')
async def roominfo_request(_, ws):
    try:
        while True:
            msg = await ws.recv()
            if msg is None:
                break
            ret = frontDesk.roomInfo()
            await ws.send(json.dumps(ret))
    except Exception as e:
        print(f"Connection error in room info: {e}")
    finally:
        print("Client disconnected from room info")

@app.websocket('/ws/manager')
async def manager_request(_, ws):
    try:
        while True:
            msg = await ws.recv()
            if msg is None:
                break
            data = json.loads(msg)
            ret = manager.show(data)
            await ws.send(json.dumps(ret))
    except Exception as e:
        print(f"Connection error in manager: {e}")
    finally:
        print("Client disconnected from manager")

@app.websocket('/ws/query_room_info')
async def query_room_info_request(_, ws):
    try:
        while True:
            msg = await ws.recv()
            if msg is None:
                break
            data = json.loads(msg)
            ret = airconSchedule.queryRoomInfo(data)
            await ws.send(json.dumps(ret))
    except Exception as e:
        print(f"Connection error in query room info: {e}")
    finally:
        print("Client disconnected from query room info")

@app.websocket('/ws/query_schedule')
async def query_schedule_request(_, ws):
    try:
        while True:
            msg = await ws.recv()
            if msg is None:
                break
            ret = airconSchedule.querySchedule()
            await ws.send(json.dumps(ret))
    except Exception as e:
        print(f"Connection error in query schedule: {e}")
    finally:
        print("Client disconnected from query schedule")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10043)