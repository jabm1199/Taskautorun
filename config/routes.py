from flask_restful import Resource, reqparse
from flask import current_app as app
from task_manager import TaskManager
import logging
import inspect
import tasks

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

def register_routes(api, scheduler):
    task_manager.set_scheduler(scheduler)
    
    api.add_resource(TaskListAPI, '/api/tasks')
    api.add_resource(TaskAPI, '/api/tasks/<string:task_id>')
    api.add_resource(TaskStartAPI, '/api/tasks/<string:task_id>/start')
    api.add_resource(TaskStopAPI, '/api/tasks/<string:task_id>/stop')
    api.add_resource(TaskExecuteAPI, '/api/tasks/<string:task_id>/execute')
    api.add_resource(TaskFunctionsAPI, '/api/functions') 