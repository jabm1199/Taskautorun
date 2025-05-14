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
import requests
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)

# HTTP请求函数
def http_request(url, method='GET', headers=None, body=None, timeout=30, verify=True, task_id=None):
    """执行HTTP请求
    
    Args:
        url: 请求URL
        method: 请求方法（GET, POST, PUT, DELETE等）
        headers: 请求头（字典）
        body: 请求体（字典或字符串）
        timeout: 超时时间（秒）
        verify: 是否验证SSL证书
        task_id: 任务ID，用于日志记录
        
    Returns:
        包含响应状态码、响应头和响应体的字典
    """
    logger = logging.getLogger('task_logger')
    method = method.upper()
    if headers is None:
        headers = {}
    
    # 构建日志前缀，确保所有日志条目包含任务ID
    task_prefix = f"[任务ID: {task_id}] " if task_id else ""
    
    # 记录请求开始信息
    logger.info(f"{task_prefix}开始执行HTTP请求: {method} {url}")
    logger.info(f"{task_prefix}请求头: {headers}")
    
    # 根据请求类型记录请求体（如果有）
    if method not in ['GET', 'HEAD', 'OPTIONS'] and body is not None:
        if isinstance(body, dict):
            logger.info(f"{task_prefix}请求体(JSON): {body}")
        else:
            log_body = body[:1000] + '...' if len(str(body)) > 1000 else body
            logger.info(f"{task_prefix}请求体: {log_body}")
    
    logger.info(f"{task_prefix}超时设置: {timeout}秒, SSL验证: {'启用' if verify else '禁用'}")
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=body if isinstance(body, dict) else None,
            data=body if not isinstance(body, dict) and body is not None else None,
            timeout=timeout,
            verify=verify
        )
        
        # 记录响应信息
        logger.info(f"{task_prefix}收到响应: 状态码 {response.status_code}")
        logger.info(f"{task_prefix}响应头: {dict(response.headers)}")
        
        # 记录响应内容，但限制长度
        try:
            # 尝试作为JSON解析
            response_json = response.json()
            logger.info(f"{task_prefix}响应内容(JSON): {response_json}")
            response_text = "已作为JSON处理，详见上方日志"
        except:
            # 如果不是JSON，以文本形式记录，并限制长度
            response_text = response.text
            if len(response_text) > 2000:
                logger.info(f"{task_prefix}响应内容(前2000字符): {response_text[:2000]}...")
                logger.info(f"{task_prefix}响应内容过长，已截断")
            else:
                logger.info(f"{task_prefix}响应内容: {response_text}")
        
        result = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': response.text,
            'success': response.status_code < 400
        }
        
        logger.info(f"{task_prefix}HTTP请求完成: {'成功' if result['success'] else '失败'}")
        return result
    except Exception as e:
        error_msg = str(e)
        logger.error(f"{task_prefix}HTTP请求发生错误: {error_msg}")
        return {
            'error': error_msg,
            'success': False
        }

class TaskGroup:
    """任务组类，用于管理一组按顺序执行的任务"""
    
    def __init__(self, group_id, name, task_ids=None, scheduler=None, task_manager=None):
        self.id = group_id
        self.name = name
        self.task_ids = task_ids or []  # 按顺序存储的任务ID列表
        self.status = 'created'  # created, running, stopped, completed, error
        self.job_id = None
        self.created_at = datetime.datetime.now().isoformat()
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.current_task_index = 0  # 当前执行到的任务索引
        self.scheduler = scheduler
        self.task_manager = task_manager
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'name': self.name,
            'task_ids': self.task_ids,
            'status': self.status,
            'job_id': self.job_id,
            'created_at': self.created_at,
            'last_run': self.last_run,
            'next_run': self.next_run,
            'run_count': self.run_count,
            'current_task_index': self.current_task_index
        }
    
    def add_task(self, task_id):
        """添加任务到任务组"""
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)
        return self.to_dict()
    
    def remove_task(self, task_id):
        """从任务组中移除任务"""
        if task_id in self.task_ids:
            self.task_ids.remove(task_id)
        return self.to_dict()
    
    def reorder_tasks(self, task_ids):
        """重新排序任务组中的任务"""
        # 确保所有提供的任务ID都在当前任务组中
        if all(task_id in self.task_ids for task_id in task_ids) and len(task_ids) == len(self.task_ids):
            self.task_ids = task_ids
        return self.to_dict()

class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.task_groups = {}  # 存储任务组
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
    
    # 任务组相关方法
    def create_task_group(self, name, task_ids=None):
        """创建新的任务组
        
        Args:
            name: 任务组名称
            task_ids: 要添加到任务组的任务ID列表（按执行顺序）
        
        Returns:
            包含任务组ID的字典
        """
        # 验证所有任务ID是否存在
        if task_ids:
            for task_id in task_ids:
                if task_id not in self.tasks:
                    return {'error': f'任务ID {task_id} 不存在'}, 404
        
        group_id = str(uuid.uuid4())
        task_group = TaskGroup(
            group_id=group_id,
            name=name,
            task_ids=task_ids or [],
            scheduler=self.scheduler,
            task_manager=self
        )
        
        self.task_groups[group_id] = task_group
        self.task_logger.info(f"创建了新任务组: {name} (ID: {group_id})")
        
        return {'id': group_id, 'status': 'created'}
    
    def get_all_task_groups(self):
        """获取所有任务组"""
        return {'task_groups': [group.to_dict() for group in self.task_groups.values()]}
    
    def get_task_group(self, group_id):
        """获取特定任务组的详情"""
        task_group = self.task_groups.get(group_id)
        if not task_group:
            return {'error': '任务组不存在'}, 404
        
        # 如果任务组正在运行中，更新下次运行时间
        if task_group.status == 'running' and task_group.job_id:
            job = self.scheduler.get_job(task_group.job_id)
            if job:
                task_group.next_run = job.next_run_time.isoformat() if job.next_run_time else None
        
        return task_group.to_dict()
    
    def update_task_group(self, group_id, data):
        """更新任务组配置"""
        task_group = self.task_groups.get(group_id)
        if not task_group:
            return {'error': '任务组不存在'}, 404
        
        # 如果任务组在运行，先停止
        if task_group.status == 'running':
            self.stop_task_group(group_id)
        
        # 更新任务组名称
        if 'name' in data and data['name']:
            task_group.name = data['name']
        
        # 更新任务列表
        if 'task_ids' in data and isinstance(data['task_ids'], list):
            # 验证所有任务ID是否存在
            for task_id in data['task_ids']:
                if task_id not in self.tasks:
                    return {'error': f'任务ID {task_id} 不存在'}, 404
            
            task_group.task_ids = data['task_ids']
        
        self.task_logger.info(f"更新了任务组配置: {task_group.name} (ID: {group_id})")
        return task_group.to_dict()
    
    def delete_task_group(self, group_id):
        """删除任务组"""
        task_group = self.task_groups.get(group_id)
        if not task_group:
            return {'error': '任务组不存在'}, 404
        
        # 如果任务组在运行，先停止
        if task_group.status == 'running':
            self.stop_task_group(group_id)
        
        # 从任务组列表中删除
        del self.task_groups[group_id]
        
        self.task_logger.info(f"删除了任务组: {task_group.name} (ID: {group_id})")
        return {'status': 'deleted'}
    
    def add_task_to_group(self, group_id, task_id):
        """将任务添加到任务组中"""
        task_group = self.task_groups.get(group_id)
        if not task_group:
            return {'error': '任务组不存在'}, 404
        
        if task_id not in self.tasks:
            return {'error': '任务不存在'}, 404
        
        result = task_group.add_task(task_id)
        self.task_logger.info(f"将任务 {task_id} 添加到任务组: {task_group.name} (ID: {group_id})")
        return result
    
    def remove_task_from_group(self, group_id, task_id):
        """从任务组中移除任务"""
        task_group = self.task_groups.get(group_id)
        if not task_group:
            return {'error': '任务组不存在'}, 404
        
        result = task_group.remove_task(task_id)
        self.task_logger.info(f"从任务组 {task_group.name} (ID: {group_id}) 中移除任务 {task_id}")
        return result
    
    def reorder_tasks_in_group(self, group_id, task_ids):
        """重新排序任务组中的任务"""
        task_group = self.task_groups.get(group_id)
        if not task_group:
            return {'error': '任务组不存在'}, 404
        
        # 验证所有任务ID是否在任务组中
        for task_id in task_ids:
            if task_id not in task_group.task_ids:
                return {'error': f'任务ID {task_id} 不在任务组中'}, 400
        
        # 验证任务数量是否匹配
        if len(task_ids) != len(task_group.task_ids):
            return {'error': '任务数量不匹配'}, 400
        
        result = task_group.reorder_tasks(task_ids)
        self.task_logger.info(f"重新排序任务组 {task_group.name} (ID: {group_id}) 中的任务")
        return result
    
    def start_task_group(self, group_id, config):
        """启动任务组
        
        Args:
            group_id: 任务组ID
            config: 包含任务配置的字典，如开始时间、结束时间、间隔等
        """
        task_group = self.task_groups.get(group_id)
        if not task_group:
            return {'error': '任务组不存在'}, 404
        
        if task_group.status == 'running':
            return {'error': '任务组已在运行中'}, 400
        
        if not task_group.task_ids:
            return {'error': '任务组中没有任务'}, 400
        
        # 构建触发器
        trigger = self._build_trigger(config)
        # 检查触发器是否为字典类型，如果是则说明返回了错误信息
        if isinstance(trigger, dict) and 'error' in trigger:
            return trigger, 400
        
        # 定义任务组执行包装函数
        def group_job_func():
            task_group.last_run = datetime.datetime.now().isoformat()
            task_group.run_count += 1
            task_group.current_task_index = 0
            task_group.status = 'running'
            
            self.task_logger.info(f"开始执行定时任务组: {task_group.name} (ID: {group_id}), 包含 {len(task_group.task_ids)} 个任务")
            
            # 执行第一个任务
            self._execute_next_task_in_group(task_group)
            
            return True
        
        # 添加任务组到调度器
        job = self.scheduler.add_job(
            group_job_func,
            trigger=trigger,
            id=f"group_{group_id}",
            name=f"TaskGroup: {task_group.name}"
        )
        
        # 更新任务组状态
        task_group.status = 'running'
        task_group.job_id = job.id
        task_group.next_run = job.next_run_time.isoformat() if job.next_run_time else None
        
        # 存储配置
        trigger_info = ""
        if 'interval' in config and config['interval']:
            task_group.interval = config['interval']
            trigger_info = f"间隔执行 {config['interval']} 秒"
        if 'cron' in config and config['cron']:
            task_group.cron = config['cron']
            trigger_info = f"Cron表达式: {config['cron']}"
        if 'start_time' in config and config['start_time']:
            task_group.start_time = config['start_time']
        if 'end_time' in config and config['end_time']:
            task_group.end_time = config['end_time']
            
        self.task_logger.info(f"启动了任务组: {task_group.name} (ID: {group_id}), {trigger_info}, 下次执行时间: {task_group.next_run}")
        return task_group.to_dict()
    
    def _execute_next_task_in_group(self, task_group):
        """执行任务组中的下一个任务
        
        当一个任务执行完成后，会调用此方法执行下一个任务
        """
        # 检查是否所有任务都已执行完毕
        if task_group.current_task_index >= len(task_group.task_ids):
            task_group.status = 'completed'
            self.task_logger.info(f"任务组执行完成: {task_group.name} (ID: {task_group.id})")
            return
        
        # 获取当前要执行的任务ID
        task_id = task_group.task_ids[task_group.current_task_index]
        task = self.tasks.get(task_id)
        
        if not task:
            self.task_logger.error(f"任务组 {task_group.name} (ID: {task_group.id}) 中的任务不存在: {task_id}")
            task_group.status = 'error'
            return
        
        # 查找并导入函数
        func = self._get_function(task['function'])
        if not func:
            self.task_logger.error(f"任务组 {task_group.name} (ID: {task_group.id}) 中的任务函数不存在: {task['function']}")
            task_group.status = 'error'
            return
        
        try:
            self.task_logger.info(f"任务组 {task_group.name} (ID: {task_group.id}) 正在执行任务 {task_group.current_task_index + 1}/{len(task_group.task_ids)}: {task['name']} (ID: {task_id})")
            
            # 更新任务的执行次数和最后执行时间
            task['last_run'] = datetime.datetime.now().isoformat()
            task['run_count'] += 1
            
            # 执行任务
            # 如果是HTTP请求函数，传递任务ID
            if task['function'] == 'http_request':
                # 复制参数并添加task_id
                args = task['args'].copy()
                args['task_id'] = task_id
                result = func(**args)
            else:
                result = func(**task['args'])
            
            # 优化HTTP请求任务结果的记录
            if task['function'] == 'http_request':
                # HTTP请求结果已经在http_request函数中记录，这里只添加一个执行成功的日志
                status_code = result.get('status_code', 'N/A')
                success = '成功' if result.get('success', False) else '失败'
                self.task_logger.info(f"任务组 {task_group.name} (ID: {task_group.id}) 中的HTTP请求任务执行完成: {task['name']} (ID: {task_id}), 状态: {success}, 状态码: {status_code}")
            else:
                # 其他类型的任务，记录完整结果
                self.task_logger.info(f"任务组 {task_group.name} (ID: {task_group.id}) 中的任务执行成功: {task['name']} (ID: {task_id}), 结果: {str(result)[:100]}")
            
            # 移动到下一个任务
            task_group.current_task_index += 1
            
            # 执行下一个任务
            self._execute_next_task_in_group(task_group)
            
        except Exception as e:
            error_msg = f"任务组 {task_group.name} (ID: {task_group.id}) 中的任务执行失败: {task['name']} (ID: {task_id}), 错误: {str(e)}"
            self.task_logger.error(error_msg)
            task_group.status = 'error'
    
    def stop_task_group(self, group_id):
        """停止任务组"""
        task_group = self.task_groups.get(group_id)
        if not task_group:
            return {'error': '任务组不存在'}, 404
        
        if task_group.status != 'running':
            return {'error': '任务组未运行'}, 400
        
        # 从调度器中移除任务组
        if task_group.job_id:
            self.scheduler.remove_job(task_group.job_id)
        
        # 更新任务组状态
        task_group.status = 'stopped'
        task_group.next_run = None
        
        self.task_logger.info(f"停止了任务组: {task_group.name} (ID: {group_id})")
        return task_group.to_dict()
    
    def execute_task_group_now(self, group_id):
        """立即执行任务组"""
        task_group = self.task_groups.get(group_id)
        if not task_group:
            return {'error': '任务组不存在'}, 404
        
        if not task_group.task_ids:
            return {'error': '任务组中没有任务'}, 400
        
        if task_group.status == 'running':
            return {'error': '任务组已在运行中'}, 400
        
        # 先检查所有任务是否存在
        for task_id in task_group.task_ids:
            if task_id not in self.tasks:
                error_msg = f"任务组 {task_group.name} (ID: {group_id}) 中的任务不存在: {task_id}"
                self.task_logger.error(error_msg)
                task_group.status = 'error'
                return {
                    'error': error_msg,
                    'status': 'error',
                    'task_group': task_group.to_dict()
                }, 400
        
        # 设置执行状态
        task_group.status = 'running'
        task_group.last_run = datetime.datetime.now().isoformat()
        task_group.run_count += 1
        task_group.current_task_index = 0
        
        self.task_logger.info(f"开始立即执行任务组: {task_group.name} (ID: {group_id}), 包含 {len(task_group.task_ids)} 个任务")
        
        # 在新线程中执行任务组，避免阻塞当前请求
        import threading
        def run_group():
            try:
                self._execute_next_task_in_group(task_group)
            except Exception as e:
                self.task_logger.error(f"任务组执行出错: {task_group.name} (ID: {group_id}), 错误: {str(e)}")
                task_group.status = 'error'
        
        thread = threading.Thread(target=run_group)
        thread.daemon = True
        thread.start()
        
        # 返回结果中包含更新后的任务组状态，以便前端能正确显示
        return {
            'status': 'executing', 
            'message': f'正在执行任务组: {task_group.name} (ID: {group_id})',
            'task_group': task_group.to_dict()
        }

    # 以下是原来的任务相关方法
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
        
        # 从所有包含该任务的任务组中移除该任务
        affected_groups = []
        for group_id, task_group in self.task_groups.items():
            if task_id in task_group.task_ids:
                task_group.task_ids.remove(task_id)
                affected_groups.append({
                    'id': group_id,
                    'name': task_group.name
                })
                self.task_logger.info(f"由于任务被删除，已从任务组 {task_group.name} (ID: {group_id}) 中移除任务 {task_id}")
        
        # 从任务列表中删除
        del self.tasks[task_id]
        
        self.task_logger.info(f"删除了任务: {task['name']} (ID: {task_id})")
        
        # 返回删除结果和受影响的任务组
        return {
            'status': 'deleted',
            'affected_groups': affected_groups
        }
    
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
                
                # 如果是HTTP请求函数，传递任务ID
                if task['function'] == 'http_request':
                    # 复制参数并添加task_id
                    args = task['args'].copy()
                    args['task_id'] = task_id
                    result = func(**args)
                else:
                    result = func(**task['args'])
                
                # 优化HTTP请求任务结果的记录
                if task['function'] == 'http_request':
                    # HTTP请求结果已经在http_request函数中记录，这里只添加一个执行成功的日志
                    status_code = result.get('status_code', 'N/A')
                    success = '成功' if result.get('success', False) else '失败'
                    self.task_logger.info(f"HTTP请求任务执行完成: {task['name']} (ID: {task_id}), 状态: {success}, 状态码: {status_code}")
                else:
                    # 其他类型的任务，记录完整结果
                    self.task_logger.info(f"任务执行成功: {task['name']} (ID: {task_id}), 结果: {result}")
                
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
            
            # 如果是HTTP请求函数，传递任务ID
            if task['function'] == 'http_request':
                # 复制参数并添加task_id
                args = task['args'].copy()
                args['task_id'] = task_id
                result = func(**args)
            else:
                result = func(**task['args'])
            
            # 优化HTTP请求任务结果的记录
            if task['function'] == 'http_request':
                # HTTP请求结果已经在http_request函数中记录，这里只添加一个执行成功的日志
                status_code = result.get('status_code', 'N/A')
                success = '成功' if result.get('success', False) else '失败'
                self.task_logger.info(f"HTTP请求任务执行完成: {task['name']} (ID: {task_id}), 状态: {success}, 状态码: {status_code}")
            else:
                # 其他类型的任务，记录完整结果
                self.task_logger.info(f"立即执行任务成功: {task['name']} (ID: {task_id}), 结果: {result}")
            
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
        # 检查是否是HTTP请求
        if function_name == 'http_request':
            return http_request
            
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