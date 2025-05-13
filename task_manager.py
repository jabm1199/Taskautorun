import uuid
import logging
import datetime
from flask import jsonify
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
import importlib
import inspect
import os
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.scheduler = None
        self.task_logger = self._setup_task_logger()
    
    def _setup_task_logger(self):
        """设置专用于任务的日志记录器"""
        # 获取已经在app.py中配置好的任务日志记录器
        task_logger = logging.getLogger('task_logger')
        
        # 如果没有处理器（可能是独立测试时），则添加一个
        if not task_logger.handlers:
            # 确保logs目录存在
            os.makedirs('logs', exist_ok=True)
            
            # 创建日志处理器，明确指定UTF-8编码
            handler = RotatingFileHandler('logs/tasks.log', maxBytes=1024*1024, 
                                        backupCount=3, encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            task_logger.addHandler(handler)
            task_logger.setLevel(logging.INFO)
        
        return task_logger
    
    def set_scheduler(self, scheduler):
        """设置调度器"""
        self.scheduler = scheduler
    
    def create_task(self, name, function_name, args=None):
        """创建新任务
        
        Args:
            name: 任务名称
            function_name: 要执行的函数名
            args: 函数参数
        
        Returns:
            包含任务ID的字典
        """
        if args is None:
            args = {}
        
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            'id': task_id,
            'name': name,
            'function': function_name,
            'args': args,
            'status': 'created',
            'job_id': None,
            'created_at': datetime.datetime.now().isoformat(),
            'last_run': None,
            'next_run': None,
            'run_count': 0
        }
        
        self.task_logger.info(f"创建了新任务: {name} (ID: {task_id})")
        return {'id': task_id, 'status': 'created'}
    
    def get_all_tasks(self):
        """获取所有任务"""
        return {'tasks': list(self.tasks.values())}
    
    def get_task(self, task_id):
        """获取特定任务的详情"""
        task = self.tasks.get(task_id)
        if not task:
            return {'error': '任务不存在'}, 404
        
        # 如果任务正在运行中，更新下次运行时间
        if task['status'] == 'running' and task['job_id']:
            job = self.scheduler.get_job(task['job_id'])
            if job:
                task['next_run'] = job.next_run_time.isoformat() if job.next_run_time else None
        
        return task
    
    def update_task(self, task_id, data):
        """更新任务配置"""
        task = self.tasks.get(task_id)
        if not task:
            return {'error': '任务不存在'}, 404
        
        # 如果任务在运行，先停止
        if task['status'] == 'running':
            self.stop_task(task_id)
        
        # 更新任务配置
        for key, value in data.items():
            if key in ['start_time', 'end_time', 'interval', 'cron'] and value is not None:
                task[key] = value
        
        self.task_logger.info(f"更新了任务配置: {task['name']} (ID: {task_id})")
        return task
    
    def delete_task(self, task_id):
        """删除任务"""
        task = self.tasks.get(task_id)
        if not task:
            return {'error': '任务不存在'}, 404
        
        # 如果任务在运行，先停止
        if task['status'] == 'running':
            self.stop_task(task_id)
        
        # 从任务列表中删除
        del self.tasks[task_id]
        
        self.task_logger.info(f"删除了任务: {task['name']} (ID: {task_id})")
        return {'status': 'deleted'}
    
    def start_task(self, task_id, config):
        """启动任务
        
        Args:
            task_id: 任务ID
            config: 包含任务配置的字典，如开始时间、结束时间、间隔等
        """
        task = self.tasks.get(task_id)
        if not task:
            return {'error': '任务不存在'}, 404
        
        if task['status'] == 'running':
            return {'error': '任务已在运行中'}, 400
        
        # 构建触发器
        trigger = self._build_trigger(config)
        # 检查触发器是否为字典类型，如果是则说明返回了错误信息
        if isinstance(trigger, dict) and 'error' in trigger:
            return trigger, 400
        
        # 查找并导入函数
        func = self._get_function(task['function'])
        if not func:
            return {'error': f"找不到函数: {task['function']}"}, 400
        
        # 定义任务执行包装函数
        def job_func():
            task['last_run'] = datetime.datetime.now().isoformat()
            task['run_count'] += 1
            
            try:
                self.task_logger.info(f"正在执行任务: {task['name']} (ID: {task_id})")
                result = func(**task['args'])
                self.task_logger.info(f"任务执行成功: {task['name']} (ID: {task_id})")
                return result
            except Exception as e:
                self.task_logger.error(f"任务执行失败: {task['name']} (ID: {task_id}), 错误: {str(e)}")
                return None
        
        # 添加任务到调度器
        job = self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id=task_id,
            name=task['name']
        )
        
        # 更新任务状态
        task['status'] = 'running'
        task['job_id'] = job.id
        task['next_run'] = job.next_run_time.isoformat() if job.next_run_time else None
        
        if 'interval' in config and config['interval']:
            task['interval'] = config['interval']
        if 'cron' in config and config['cron']:
            task['cron'] = config['cron']
        if 'start_time' in config and config['start_time']:
            task['start_time'] = config['start_time']
        if 'end_time' in config and config['end_time']:
            task['end_time'] = config['end_time']
            
        self.task_logger.info(f"启动了任务: {task['name']} (ID: {task_id})")
        return task
    
    def stop_task(self, task_id):
        """停止任务"""
        task = self.tasks.get(task_id)
        if not task:
            return {'error': '任务不存在'}, 404
        
        if task['status'] != 'running':
            return {'error': '任务未运行'}, 400
        
        # 从调度器中移除任务
        self.scheduler.remove_job(task['job_id'])
        
        # 更新任务状态
        task['status'] = 'stopped'
        task['next_run'] = None
        
        self.task_logger.info(f"停止了任务: {task['name']} (ID: {task_id})")
        return task
    
    def execute_task_now(self, task_id):
        """立即执行一次任务"""
        task = self.tasks.get(task_id)
        if not task:
            return {'error': '任务不存在'}, 404
        
        # 查找并导入函数
        func = self._get_function(task['function'])
        if not func:
            return {'error': f"找不到函数: {task['function']}"}, 400
        
        # 执行任务
        task['last_run'] = datetime.datetime.now().isoformat()
        task['run_count'] += 1
        
        try:
            self.task_logger.info(f"立即执行任务: {task['name']} (ID: {task_id})")
            result = func(**task['args'])
            self.task_logger.info(f"立即执行任务成功: {task['name']} (ID: {task_id})")
            return {'status': 'executed', 'result': str(result)}
        except Exception as e:
            error_msg = f"立即执行任务失败: {task['name']} (ID: {task_id}), 错误: {str(e)}"
            self.task_logger.error(error_msg)
            return {'error': error_msg}, 500
    
    def _build_trigger(self, config):
        """构建任务触发器
        
        Args:
            config: 包含任务配置的字典
        
        Returns:
            触发器对象或包含错误信息的字典
        """
        # 间隔触发
        if 'interval' in config and config['interval']:
            trigger = IntervalTrigger(
                seconds=config['interval'],
                start_date=config.get('start_time'),
                end_date=config.get('end_time')
            )
            return trigger
        
        # Cron表达式触发
        if 'cron' in config and config['cron']:
            try:
                trigger = CronTrigger.from_crontab(
                    config['cron'],
                    start_date=config.get('start_time'),
                    end_date=config.get('end_time')
                )
                return trigger
            except ValueError as e:
                return {'error': f"无效的Cron表达式: {str(e)}"}
        
        # 单次触发
        if 'start_time' in config and config['start_time']:
            trigger = DateTrigger(run_date=config['start_time'])
            return trigger
        
        return {'error': '缺少触发器配置'}
    
    def _get_function(self, function_name):
        """根据函数名查找并返回函数对象"""
        try:
            # 支持形如 'module.submodule.function' 的函数名
            parts = function_name.split('.')
            module_name = '.'.join(parts[:-1])
            func_name = parts[-1]
            
            # 如果是一个简单的函数名，尝试在内置任务模块中查找
            if not module_name:
                try:
                    import tasks
                    if hasattr(tasks, func_name):
                        return getattr(tasks, func_name)
                except ImportError:
                    pass
                
                # 再检查内置函数
                import builtins
                if hasattr(builtins, func_name):
                    return getattr(builtins, func_name)
                
                return None
            
            # 尝试导入模块
            module = importlib.import_module(module_name)
            return getattr(module, func_name)
        except (ImportError, AttributeError) as e:
            self.task_logger.error(f"找不到函数 {function_name}: {str(e)}")
            return None 