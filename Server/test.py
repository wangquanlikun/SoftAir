from CentralConditioner import *
from FrontDesk import *


cc = CentralConditioner()
fd = FrontDesk()
fd.create_accommodation_order("xht", "111")
cc.set_speed_request("201", "high")  # 最好是调试，停几面才能看出效果，后面不用停
cc.set_speed_request("201", "medium")
cc.delete_server("201")
fd.query_fee_records("xht")
