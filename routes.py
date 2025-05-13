from flask_restful import Resource, reqparse
from flask import current_app as app, jsonify, request
from task_manager import TaskManager
import logging
import inspect
import tasks
import os
import re
from datetime import datetime, timedelta

task_manager = TaskManager()

class TaskListAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('name', type=str, required=True, 
                                help='任务名称不能为空')
        self.parser.add_argument('function', type=str, required=True, 
                                help='要执行的函数名不能为空')
        self.parser.add_argument('args', type=dict, default={},
                                help='函数参数')
        super(TaskListAPI, self).__init__()
    
    def get(self):
        """获取所有任务列表"""
        return task_manager.get_all_tasks()
    
    def post(self):
        """创建新任务"""
        args = self.parser.parse_args()
        app.logger.info(f"正在创建新任务：{args['name']}")
        return task_manager.create_task(args['name'], args['function'], args['args'])

class TaskAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('start_time', type=str, 
                                help='开始时间')
        self.parser.add_argument('end_time', type=str, 
                                help='结束时间')
        self.parser.add_argument('interval', type=int, 
                                help='运行间隔（秒）')
        self.parser.add_argument('cron', type=str, 
                                help='Cron表达式')
        super(TaskAPI, self).__init__()
    
    def get(self, task_id):
        """获取任务详情"""
        return task_manager.get_task(task_id)
    
    def put(self, task_id):
        """更新任务"""
        args = self.parser.parse_args()
        app.logger.info(f"正在更新任务 {task_id}")
        return task_manager.update_task(task_id, args)
    
    def delete(self, task_id):
        """删除任务"""
        app.logger.info(f"正在删除任务 {task_id}")
        return task_manager.delete_task(task_id)

class TaskStartAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('start_time', type=str, 
                                help='开始时间 (ISO 格式 YYYY-MM-DD HH:MM:SS)')
        self.parser.add_argument('end_time', type=str, 
                                help='结束时间 (ISO 格式 YYYY-MM-DD HH:MM:SS)')
        self.parser.add_argument('interval', type=int, 
                                help='运行间隔（秒）')
        self.parser.add_argument('cron', type=str, 
                                help='Cron表达式 (例如: "*/5 * * * *")')
        super(TaskStartAPI, self).__init__()
    
    def post(self, task_id):
        """启动任务"""
        args = self.parser.parse_args()
        app.logger.info(f"正在启动任务 {task_id}")
        return task_manager.start_task(task_id, args)

class TaskStopAPI(Resource):
    def post(self, task_id):
        """停止任务"""
        app.logger.info(f"正在停止任务 {task_id}")
        return task_manager.stop_task(task_id)

class TaskExecuteAPI(Resource):
    def post(self, task_id):
        """立即执行任务"""
        app.logger.info(f"正在立即执行任务 {task_id}")
        return task_manager.execute_task_now(task_id)

class TaskFunctionsAPI(Resource):
    def get(self):
        """获取可用的任务函数列表"""
        functions = []
        
        # 获取tasks模块中的所有函数
        for name, func in inspect.getmembers(tasks, inspect.isfunction):
            # 获取函数文档
            doc = inspect.getdoc(func) or name
            
            # 获取函数参数
            signature = inspect.signature(func)
            params = []
            for param_name, param in signature.parameters.items():
                param_info = {'name': param_name}
                if param.default != inspect.Parameter.empty:
                    param_info['default'] = param.default
                params.append(param_info)
            
            functions.append({
                'name': name,
                'description': doc,
                'parameters': params
            })
        
        app.logger.info(f"获取可用的任务函数列表，共{len(functions)}个")
        return {'functions': functions}

class TaskLogsAPI(Resource):
    def get(self, task_id=None):
        """获取任务执行日志
        
        参数:
            task_id: 任务ID，如果不提供则获取所有日志
            lines: 获取的日志行数，默认100
            days: 获取最近几天的日志，默认1
        """
        lines = request.args.get('lines', default=100, type=int)
        days = request.args.get('days', default=1, type=int)
        
        log_file = 'logs/tasks.log'
        if not os.path.exists(log_file):
            return {'logs': [], 'error': '日志文件不存在'}, 404
        
        # 获取日志文件最后N行
        try:
            # 首先尝试使用 utf-8 编码但忽略错误
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                logs = f.readlines()
        except UnicodeError:
            try:
                # 如果还有问题，尝试使用 GBK 编码
                with open(log_file, 'r', encoding='gbk', errors='ignore') as f:
                    logs = f.readlines()
            except Exception as e:
                app.logger.error(f"读取日志文件失败: {e}")
                return {'logs': [], 'error': f'读取日志文件失败: {str(e)}'}, 500
        except Exception as e:
            app.logger.error(f"读取日志文件失败: {e}")
            return {'logs': [], 'error': f'读取日志文件失败: {str(e)}'}, 500
        
        # 根据天数过滤
        if days > 0:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            logs = [log for log in logs if log.startswith(cutoff_date) or log.split(' ')[0] >= cutoff_date]
        
        # 根据任务ID过滤
        if task_id:
            task = task_manager.get_task(task_id)
            if isinstance(task, tuple) and task[1] == 404:
                return {'logs': [], 'error': '任务不存在'}, 404
                
            task_name = task['name']
            task_pattern = f"ID: {task_id}"
            
            # 备份原始日志，以便在第一次过滤失败时使用
            logs_backup = logs.copy()
            logs = [log for log in logs if task_pattern in log]
            
            # 如果没有找到日志，尝试使用任务名称作为备选过滤方式
            if not logs:
                app.logger.info(f"没有找到包含ID: {task_id}的日志，尝试使用任务名称过滤")
                task_name_pattern = f"{task_name}"
                logs = [log for log in logs_backup if task_name_pattern in log]
        
        # 限制返回行数
        logs = logs[-lines:] if lines > 0 else logs
        
        # 格式化日志
        formatted_logs = []
        for log in logs:
            try:
                # 移除尾部的换行符
                log_line = log.strip()
                if not log_line:
                    continue
                    
                # 尝试分割日志行
                parts = log_line.split(' - ', 2)
                if len(parts) >= 3:
                    timestamp, level, message = parts
                    formatted_logs.append({
                        'timestamp': timestamp,
                        'level': level.strip(),
                        'message': message.strip()
                    })
                else:
                    # 如果无法按预期格式分割，尝试其他常见的日志格式
                    # 例如检查是否有日期时间格式的开头
                    import re
                    date_match = re.match(r'^\d{4}-\d{2}-\d{2}', log_line)
                    if date_match:
                        # 尝试提取时间戳
                        date_end = log_line.find(' ', 10)  # 找第一个空格在日期之后
                        if date_end > 0:
                            timestamp = log_line[:date_end]
                            rest = log_line[date_end+1:].strip()
                            
                            # 尝试查找日志级别
                            level_matches = re.search(r'\b(INFO|ERROR|WARNING|DEBUG|CRITICAL)\b', rest)
                            if level_matches:
                                level = level_matches.group(0)
                                message = rest.replace(level, '', 1).strip()
                            else:
                                level = 'INFO'
                                message = rest
                                
                            formatted_logs.append({
                                'timestamp': timestamp,
                                'level': level,
                                'message': message
                            })
                        else:
                            formatted_logs.append({
                                'timestamp': '',
                                'level': 'INFO',
                                'message': log_line
                            })
                    else:
                        formatted_logs.append({
                            'timestamp': '',
                            'level': 'INFO',
                            'message': log_line
                        })
            except Exception as e:
                app.logger.error(f"解析日志行出错: {e}, 原始日志行: {log[:100]}...")
                formatted_logs.append({
                    'timestamp': '',
                    'level': 'ERROR',
                    'message': f"[解析错误] {log_line}"
                })
        
        return {'logs': formatted_logs}

def register_routes(api, scheduler):
    task_manager.set_scheduler(scheduler)
    
    api.add_resource(TaskListAPI, '/api/tasks')
    api.add_resource(TaskAPI, '/api/tasks/<string:task_id>')
    api.add_resource(TaskStartAPI, '/api/tasks/<string:task_id>/start')
    api.add_resource(TaskStopAPI, '/api/tasks/<string:task_id>/stop')
    api.add_resource(TaskExecuteAPI, '/api/tasks/<string:task_id>/execute')
    api.add_resource(TaskFunctionsAPI, '/api/functions')
    api.add_resource(TaskLogsAPI, '/api/logs', '/api/logs/<string:task_id>') 