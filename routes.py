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

# 任务组API相关类
class TaskGroupListAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('name', type=str, required=True, 
                                help='任务组名称不能为空')
        self.parser.add_argument('task_ids', type=list, default=[],
                                help='任务ID列表')
        super(TaskGroupListAPI, self).__init__()
    
    def get(self):
        """获取所有任务组列表"""
        return task_manager.get_all_task_groups()
    
    def post(self):
        """创建新任务组"""
        args = self.parser.parse_args()
        app.logger.info(f"正在创建新任务组：{args['name']}")
        return task_manager.create_task_group(args['name'], args['task_ids'])

class TaskGroupAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('name', type=str, 
                                help='任务组名称')
        self.parser.add_argument('task_ids', type=list, 
                                help='任务ID列表')
        super(TaskGroupAPI, self).__init__()
    
    def get(self, group_id):
        """获取任务组详情"""
        return task_manager.get_task_group(group_id)
    
    def put(self, group_id):
        """更新任务组"""
        args = self.parser.parse_args()
        app.logger.info(f"正在更新任务组 {group_id}")
        return task_manager.update_task_group(group_id, args)
    
    def delete(self, group_id):
        """删除任务组"""
        app.logger.info(f"正在删除任务组 {group_id}")
        return task_manager.delete_task_group(group_id)

class TaskGroupTaskAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('task_id', type=str, required=True,
                                help='任务ID不能为空')
        super(TaskGroupTaskAPI, self).__init__()
    
    def post(self, group_id):
        """添加任务到任务组"""
        args = self.parser.parse_args()
        app.logger.info(f"正在向任务组 {group_id} 添加任务 {args['task_id']}")
        return task_manager.add_task_to_group(group_id, args['task_id'])
    
    def delete(self, group_id):
        """从任务组中移除任务"""
        args = self.parser.parse_args()
        app.logger.info(f"正在从任务组 {group_id} 移除任务 {args['task_id']}")
        return task_manager.remove_task_from_group(group_id, args['task_id'])

class TaskGroupReorderAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('task_ids', type=list, required=True,
                                help='任务ID列表不能为空')
        super(TaskGroupReorderAPI, self).__init__()
    
    def post(self, group_id):
        """重新排序任务组中的任务"""
        args = self.parser.parse_args()
        app.logger.info(f"正在重新排序任务组 {group_id} 中的任务")
        return task_manager.reorder_tasks_in_group(group_id, args['task_ids'])

class TaskGroupStartAPI(Resource):
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
        super(TaskGroupStartAPI, self).__init__()
    
    def post(self, group_id):
        """启动任务组"""
        args = self.parser.parse_args()
        app.logger.info(f"正在启动任务组 {group_id}")
        return task_manager.start_task_group(group_id, args)

class TaskGroupStopAPI(Resource):
    def post(self, group_id):
        """停止任务组"""
        app.logger.info(f"正在停止任务组 {group_id}")
        return task_manager.stop_task_group(group_id)

class TaskGroupExecuteAPI(Resource):
    def post(self, group_id):
        """立即执行任务组"""
        app.logger.info(f"正在立即执行任务组 {group_id}")
        return task_manager.execute_task_group_now(group_id)

# 原有的任务相关类
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
        self.parser.add_argument('name', type=str, 
                                help='任务名称')
        self.parser.add_argument('function', type=str, 
                                help='要执行的函数名')
        self.parser.add_argument('args', type=dict, 
                                help='函数参数')
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
        
        # 添加http_request函数
        http_params = [
            {'name': 'url', 'description': '请求URL'},
            {'name': 'method', 'default': 'GET', 'description': '请求方法（GET, POST, PUT, DELETE等）'},
            {'name': 'headers', 'default': {}, 'description': '请求头（字典）'},
            {'name': 'body', 'default': None, 'description': '请求体（字典或字符串）'},
            {'name': 'timeout', 'default': 30, 'description': '超时时间（秒）'},
            {'name': 'verify', 'default': True, 'description': '是否验证SSL证书'}
        ]
        
        functions.append({
            'name': 'http_request',
            'description': '执行HTTP请求\n\n可用于调用外部API、爬取网页数据或与其他系统集成',
            'parameters': http_params
        })
        
        app.logger.info(f"获取可用的任务函数列表，共{len(functions)}个")
        return {'functions': functions}

class TaskLogsAPI(Resource):
    def get(self, task_id=None):
        """获取任务执行日志
        
        参数:
            task_id: 任务ID或任务组ID，如果不提供则获取所有日志
            lines: 获取的日志行数，默认100
            days: 获取最近几天的日志，默认1
        """
        # 确保能访问re模块
        import re as regex
        
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
        
        # 备份原始日志，以便多次过滤
        logs_backup = logs.copy()
        
        # 根据ID过滤（先尝试作为任务ID查询）
        if task_id:
            # 先尝试作为任务ID处理
            task = task_manager.get_task(task_id)
            
            # 如果不是任务ID，尝试作为任务组ID处理
            if isinstance(task, tuple) and task[1] == 404:
                task_group = task_manager.get_task_group(task_id)
                
                # 如果也不是任务组ID，返回错误
                if isinstance(task_group, tuple) and task_group[1] == 404:
                    return {'logs': [], 'error': '任务或任务组不存在'}, 404
                
                # 处理任务组日志
                task_group_obj = task_manager.task_groups.get(task_id)
                if not task_group_obj:
                    return {'logs': [], 'error': '任务组不存在'}, 404
                
                # 获取任务组包含的所有任务ID
                task_ids = task_group_obj.task_ids
                
                # 任务组自身的日志模式
                task_group_pattern = f"(ID: {task_id}|任务组: {task_group_obj.name})"
                
                # 收集任务组日志和所有任务的日志
                group_logs = []
                
                # 1. 收集任务组自身相关的日志
                for log in logs:
                    if regex.search(task_group_pattern, log):
                        group_logs.append(log)
                
                # 2. 收集任务组中所有任务的日志
                for task_id_in_group in task_ids:
                    task_in_group = task_manager.tasks.get(task_id_in_group)
                    if not task_in_group:
                        continue
                    
                    task_name = task_in_group['name']
                    task_pattern = f"ID: {task_id_in_group}"
                    task_id_pattern = f"任务ID: {task_id_in_group}"
                    
                    # 找出与该任务相关的所有日志，包括HTTP请求日志
                    is_capture = False
                    i = 0
                    while i < len(logs):
                        log = logs[i]
                        
                        # 如果日志行包含任务ID，开始收集
                        if regex.search(task_pattern, log) or regex.search(task_id_pattern, log):
                            group_logs.append(log)
                            
                            # 对HTTP请求任务特殊处理，启动捕获模式
                            if "开始执行HTTP请求" in log or ("执行任务" in log and "http_request" in log):
                                is_capture = True
                        
                        # 捕获模式下收集所有HTTP请求相关日志
                        elif is_capture:
                            # 收集当前行
                            group_logs.append(log)
                            
                            # 检查是否是HTTP请求结束
                            if "HTTP请求完成" in log or "HTTP请求发生错误" in log or "HTTP请求任务执行完成" in log:
                                is_capture = False
                        
                        i += 1
                
                # 排序日志（按时间戳）
                group_logs = sorted(group_logs, key=lambda x: x.split(' - ')[0] if ' - ' in x else x)
                
                logs = group_logs
            else:
                # 处理普通任务日志
                task_name = task['name']
                task_pattern = f"ID: {task_id}"
                task_id_pattern = f"任务ID: {task_id}"
                
                # 收集与任务相关的所有日志，包括HTTP请求日志
                filtered_logs = []
                is_capture = False
                
                for i, log in enumerate(logs):
                    # 如果日志行包含任务ID，开始收集
                    if regex.search(task_pattern, log) or regex.search(task_id_pattern, log):
                        filtered_logs.append(log)
                        
                        # 对HTTP请求任务特殊处理，启动捕获模式
                        if "开始执行HTTP请求" in log or ("执行任务" in log and "http_request" in log):
                            is_capture = True
                        continue
                    
                    # 捕获模式下收集所有HTTP请求相关日志
                    if is_capture:
                        # 收集当前行
                        filtered_logs.append(log)
                        
                        # 检查是否是HTTP请求结束
                        if "HTTP请求完成" in log or "HTTP请求发生错误" in log or "HTTP请求任务执行完成" in log:
                            is_capture = False
                
                logs = filtered_logs
        
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
                    date_match = regex.match(r'^\d{4}-\d{2}-\d{2}', log_line)
                    if date_match:
                        # 尝试提取时间戳
                        date_end = log_line.find(' ', 10)  # 找第一个空格在日期之后
                        if date_end > 0:
                            timestamp = log_line[:date_end]
                            rest = log_line[date_end+1:].strip()
                            
                            # 尝试查找日志级别
                            level_matches = regex.search(r'\b(INFO|ERROR|WARNING|DEBUG|CRITICAL)\b', rest)
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
    
    def delete(self, task_id=None):
        """清除日志
        
        参数:
            task_id: 任务ID或任务组ID，如果不提供则清除所有日志
            days: 清除最近几天的日志，默认清除全部
        """
        days = request.args.get('days', default=0, type=int)
        
        log_file = 'logs/tasks.log'
        if not os.path.exists(log_file):
            return {'status': 'error', 'message': '日志文件不存在'}, 404
        
        try:
            # 首先备份日志文件
            backup_file = f'logs/tasks_backup_{datetime.now().strftime("%Y%m%d%H%M%S")}.log'
            import shutil
            shutil.copy2(log_file, backup_file)
            
            # 如果指定了任务ID，只清除相关日志
            if task_id:
                # 读取所有日志
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    logs = f.readlines()
                
                # 根据天数过滤要保留的日志
                if days > 0:
                    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                    older_logs = [log for log in logs if log.split(' ')[0] < cutoff_date]
                else:
                    older_logs = []
                
                # 先尝试作为任务ID处理
                task = task_manager.get_task(task_id)
                
                # 决定过滤条件
                if isinstance(task, tuple) and task[1] == 404:
                    # 尝试作为任务组ID处理
                    task_group = task_manager.get_task_group(task_id)
                    
                    if isinstance(task_group, tuple) and task_group[1] == 404:
                        return {'status': 'error', 'message': '任务或任务组不存在'}, 404
                    
                    # 任务组的过滤条件
                    task_name = task_group['name']
                    task_pattern = f"ID: {task_id}"
                    group_pattern = f"任务组: {task_name}"
                    
                    # 保留不包含该任务组的日志
                    if days > 0:
                        logs_to_keep = older_logs + [
                            log for log in logs 
                            if (log.split(' ')[0] >= cutoff_date) and 
                               (task_pattern not in log and group_pattern not in log and task_name not in log)
                        ]
                    else:
                        logs_to_keep = [
                            log for log in logs 
                            if (task_pattern not in log and group_pattern not in log and task_name not in log)
                        ]
                else:
                    # 任务的过滤条件
                    task_name = task['name']
                    task_pattern = f"ID: {task_id}"
                    
                    # 保留不包含该任务的日志
                    if days > 0:
                        logs_to_keep = older_logs + [
                            log for log in logs 
                            if (log.split(' ')[0] >= cutoff_date) and 
                               (task_pattern not in log and task_name not in log)
                        ]
                    else:
                        logs_to_keep = [
                            log for log in logs 
                            if (task_pattern not in log and task_name not in log)
                        ]
                
                # 写入保留的日志
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.writelines(logs_to_keep)
                
                # 记录操作日志
                operation_info = f"任务ID: {task_id}" if not isinstance(task, tuple) else f"任务组ID: {task_id}"
                days_info = f"最近{days}天" if days > 0 else "所有"
                app.logger.info(f"已清除{operation_info}的{days_info}日志")
                
                return {'status': 'success', 'message': f'已清除指定日志，备份至 {backup_file}'}
            else:
                # 清除所有日志或保留一部分
                if days > 0:
                    # 只保留早于指定天数的日志
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        logs = f.readlines()
                    
                    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                    logs_to_keep = [log for log in logs if log.split(' ')[0] < cutoff_date]
                    
                    with open(log_file, 'w', encoding='utf-8') as f:
                        f.writelines(logs_to_keep)
                else:
                    # 清空所有日志
                    open(log_file, 'w').close()
                
                days_info = f"最近{days}天" if days > 0 else "所有"
                app.logger.info(f"已清除{days_info}全局日志")
                
                return {'status': 'success', 'message': f'已清除{days_info}日志，备份至 {backup_file}'}
        
        except Exception as e:
            app.logger.error(f"清除日志失败: {e}")
            return {'status': 'error', 'message': f'清除日志失败: {str(e)}'}, 500

def register_routes(api, scheduler):
    task_manager.set_scheduler(scheduler)
    
    # 任务相关路由
    api.add_resource(TaskListAPI, '/api/tasks')
    api.add_resource(TaskAPI, '/api/tasks/<string:task_id>')
    api.add_resource(TaskStartAPI, '/api/tasks/<string:task_id>/start')
    api.add_resource(TaskStopAPI, '/api/tasks/<string:task_id>/stop')
    api.add_resource(TaskExecuteAPI, '/api/tasks/<string:task_id>/execute')
    api.add_resource(TaskFunctionsAPI, '/api/functions')
    api.add_resource(TaskLogsAPI, '/api/logs', '/api/logs/<string:task_id>')
    
    # 任务组相关路由
    api.add_resource(TaskGroupListAPI, '/api/task-groups')
    api.add_resource(TaskGroupAPI, '/api/task-groups/<string:group_id>')
    api.add_resource(TaskGroupTaskAPI, '/api/task-groups/<string:group_id>/tasks')
    api.add_resource(TaskGroupReorderAPI, '/api/task-groups/<string:group_id>/reorder')
    api.add_resource(TaskGroupStartAPI, '/api/task-groups/<string:group_id>/start')
    api.add_resource(TaskGroupStopAPI, '/api/task-groups/<string:group_id>/stop')
    api.add_resource(TaskGroupExecuteAPI, '/api/task-groups/<string:group_id>/execute') 