# create_table_query f"""
#   CREATE TABLE IF NOT EXISTS rdr
#   (
#     `房间号` VARCHAR(64),
#     `用户ID` VARCHAR(64),
#     `风速` VARCHAR(64),
#     `目标温度` DECIMAL(18,2),
#     `冷热模式` VARCHAR(664),
#     `开始时间` DATETIME,
#     `结束时间` DATETIME,
#     `费用` DECIMAL(18,2)
# );
# """
## 实现获取账单和获取详单两个函数，分别为 getbill 和 getrdr
## getbill 函数返回一个string类型字符串，内容包括用户ID、房间号以及总费用
## getrdr返回json格式的详单，根据前端发送的请求，若为usr请求，则返回该用户最近一次的住宿时间段所包含的所有详单，若为room，则返回相应房间在查询时间段的所有详单
import json
from datetime import datetime
import pymysql

class RDR:

    @staticmethod
    def getbill(roomid):
        """
        获取指定房间的账单
        
        Args:
            roomid: 房间号
            
        Returns:
            包含用户ID、房间号以及总费用的字符串
        """
        connection = None
        cursor = None
        try:
            connection = pymysql.connect(
                host="localhost", 
                user="root", 
                password="123456", 
                database="soft_air"
            )
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            # 检查表是否存在
            cursor.execute("SHOW TABLES LIKE 'clients'")
            result = cursor.fetchone()
            if not result:
                return json.dumps({"uselist": "clients表不存在"}, ensure_ascii=False)
            
            # 首先从用户表查询该房间最近的入住记录
            user_query = """
                SELECT  用户名, 用户ID, 入住时间, 结账时间, 总费用   
                FROM clients
                WHERE 房间号 = %s
                ORDER BY 入住时间 DESC
                LIMIT 1
            """
            cursor.execute(user_query, (roomid,))
            user = cursor.fetchone()

            if not user:
                return json.dumps({"uselist": "未找到用户记录"}, ensure_ascii=False)

            user_id = user['用户ID']
            room_id = roomid
            check_in_time = user['入住时间']
            check_out_time = user['结账时间']

            # 查询该房间在入住期间的所有详单记录
            rdr_query = """
                SELECT SUM(费用) as total_cost
                FROM rdr
                WHERE 房间号 = %s 
                AND 开始时间 >= %s 
                AND 结束时间 <= %s
            """
            cursor.execute(rdr_query, (room_id, check_in_time, check_out_time))
            rdr_result = cursor.fetchone()

            # 确定总费用
            if rdr_result and rdr_result['total_cost'] is not None:
                total_cost = float(rdr_result['total_cost'])
            else:
                # 如果在详单中没有找到记录，使用用户表中的账单金额
                total_cost = float(user['总费用']) if '总费用' in user and user['总费用'] is not None else 0.0

            # 构建返回字符串
            return json.dumps({"bill": total_cost})
            
        except pymysql.Error as e:
            return f"数据库错误: {e}"
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    def getrdr(roomid, type, usrid=None, start_time=None, end_time=None):
        """
        获取指定房间或用户的详单
        
        Args:
            roomid: 房间号
            type: 查询类型，usr 或 room
            usrid: 用户ID（仅在type为usr时使用）
            start_time: 查询开始时间（仅在type为room时使用）
            end_time: 查询结束时间（仅在type为room时使用）
            
        Returns:
            JSON格式的详单
        """
        connection = None
        cursor = None
        try:
            connection = pymysql.connect(
                host="localhost", 
                user="root", 
                password="123456", 
                database="soft_air"
            )
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            # 检查表是否存在
            cursor.execute("SHOW TABLES LIKE 'rdr'")
            result = cursor.fetchone()
            if not result:
                return json.dumps({"uselist": "rdr表不存在"}, ensure_ascii=False)
            
            if type == 'usr':
                # 查询该用户最近一次的住宿时间段所包含的所有详单
                user_query = """
                    SELECT 入住时间, 结账时间
                    FROM clients
                    WHERE 用户ID = %s
                    ORDER BY 入住时间 DESC
                    LIMIT 1
                """
                cursor.execute(user_query, (usrid,))
                user = cursor.fetchone()
                
                if not user:
                    return json.dumps({"uselist": "未找到用户记录"}, ensure_ascii=False)

                check_in_time = user['入住时间']
                check_out_time = user['结账时间']
                
                rdr_query = """
                    SELECT 房间号, 用户ID, 风速, 开始时间, 结束时间, 费用
                    FROM rdr
                    WHERE 用户ID = %s
                    AND 开始时间 >= %s
                    AND 结束时间 <= %s
                """
                cursor.execute(rdr_query, (usrid, check_in_time, check_out_time))
                rdr_results = cursor.fetchall()
                
                if not rdr_results:
                    return json.dumps({"uselist": "未找到详单记录"}, ensure_ascii=False)
                
                # 处理日期时间字段以便JSON序列化
                for record in rdr_results:
                    for key, value in record.items():
                        if isinstance(value, datetime):
                            record[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                
                return json.dumps(rdr_results, ensure_ascii=False)
                
            elif type == 'room':
                if not start_time or not end_time:
                    return json.dumps({"uselist": "查询房间详单需要提供开始和结束时间"}, ensure_ascii=False)
                
                rdr_query = """
                    SELECT 房间号, 用户ID, 风速, 开始时间, 结束时间, 费用
                    FROM rdr
                    WHERE 房间号 = %s
                    AND 开始时间 >= %s
                    AND 结束时间 <= %s
                """
                cursor.execute(rdr_query, (roomid, start_time, end_time))
                rdr_results = cursor.fetchall()
                
                if not rdr_results:
                    return json.dumps({"uselist": "未找到详单记录"}, ensure_ascii=False)
                
                # 处理日期时间字段以便JSON序列化
                for record in rdr_results:
                    for key, value in record.items():
                        if isinstance(value, datetime):
                            record[key] = value.strftime('%Y-%m-%d %H:%M:%S')

                return json.dumps({"uselist": rdr_results}, ensure_ascii=False)

            else:
                return json.dumps({"uselist": "无效的查询类型，仅支持'usr'或'room'"}, ensure_ascii=False)
                
        except pymysql.Error as e:
            return json.dumps({"uselist": f"数据库错误: {str(e)}"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"uselist": f"处理错误: {str(e)}"}, ensure_ascii=False)
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
                
    @staticmethod
    def get_report(start_time, end_time):
        """
        获取指定时间段内的报表
        
        Args:
            start_time: 查询开始时间
            end_time: 查询结束时间
            
        Returns:
            报表内容
        """
        connection = None
        cursor = None
        try:
            connection = pymysql.connect(
                host="localhost", 
                user="root", 
                password="123456", 
                database="soft_air"
            )
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            # 检查表是否存在
            cursor.execute("SHOW TABLES LIKE 'rdr'")
            result = cursor.fetchone()
            if not result:
                return json.dumps({"content": "rdr表不存在"})
            
            report_query = """
                SELECT 房间号, 用户ID, SUM(费用) as 总费用
                FROM rdr
                WHERE 开始时间 >= %s AND 结束时间 <= %s
                GROUP BY 房间号, 用户ID
            """
            cursor.execute(report_query, (start_time, end_time))
            report_results = cursor.fetchall()
            
            if not report_results:
                return json.dumps({"content": "未找到报表记录"})
            
            # 处理日期时间字段以便JSON序列化
            for record in report_results:
                for key, value in record.items():
                    if isinstance(value, datetime):
                        record[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            
            # 计算所有房间的总费用
            total_cost = sum(float(record['总费用']) for record in report_results)
            
            # 格式化报表内容为一个字符串
            formatted_report = f"查询时间段: {start_time} 至 {end_time}\n\n"
            formatted_report += "房间号\t用户ID\t总费用\n"
            formatted_report += "-------------------------------\n"
            
            for record in report_results:
                formatted_report += f"{record['房间号']}\t{record['用户ID']}\t¥{record['总费用']:.2f}\n"
            
            formatted_report += "===============================\n"
            formatted_report += f"总计: ¥{total_cost:.2f}"
            
            # 返回格式化的报表内容
            return json.dumps({"content": formatted_report}, ensure_ascii=False)
            
        except pymysql.Error as e:
            return json.dumps({"content": f"数据库错误: {e}"}, ensure_ascii=False)
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
                
    @staticmethod
    def get_scheduling_info():
        """
        获取当前调度信息
        
        Returns:
            当前调度信息
        """
        connection = None
        cursor = None
        try:
            connection = pymysql.connect(
                host="localhost", 
                user="root", 
                password="123456", 
                database="soft_air"
            )
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            # 检查表是否存在
            cursor.execute("SHOW TABLES LIKE 'ac_status'")
            result = cursor.fetchone()
            if not result:
                return json.dumps({"content": "ac_status表不存在"})
            
            scheduling_query = """
                SELECT 房间号, 空调状态
                FROM ac_status
                WHERE 结束时间 IS NULL
                ORDER BY 开始时间 DESC
            """
            cursor.execute(scheduling_query)
            scheduling_results = cursor.fetchall()
            
            if not scheduling_results:
                return json.dumps({"content": "未找到调度信息"})
            
            # 将房间分到服务队列和等待队列
            serving_queue = []
            waiting_queue = []
            
            for record in scheduling_results:
                room_id = record['房间号']
                status = record['空调状态']
                
                if status == 'on':
                    serving_queue.append(room_id)
                elif status == 'waiting':
                    waiting_queue.append(room_id)
            
            # 返回指定格式的调度信息
            return json.dumps({
                "serving_queue": serving_queue,
                "waiting_queue": waiting_queue
            }, ensure_ascii=False)
            
        except pymysql.Error as e:
            return json.dumps({
                "serving_queue": [],
                "waiting_queue": [],
                "error": f"数据库错误: {e}"
            }, ensure_ascii=False)
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()