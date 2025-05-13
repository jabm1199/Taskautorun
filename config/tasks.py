import time
import logging
import random
import requests
import os
from datetime import datetime

logger = logging.getLogger('task_logger')

def hello_world(name="世界"):
    """一个简单的示例任务，打印问候语"""
    message = f"你好，{name}！现在是 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    logger.info(message)
    return message

def random_number(min_val=1, max_val=100):
    """生成随机数的示例任务"""
    number = random.randint(min_val, max_val)
    logger.info(f"生成的随机数: {number}")
    return number

def fetch_weather(city="北京"):
    """获取天气示例任务"""
    try:
        # 这里使用的是模拟数据，实际应用中应替换为真实API
        weather_conditions = ["晴天", "多云", "小雨", "大雨", "雷阵雨", "雾霾"]
        temperatures = list(range(0, 40))
        
        weather = random.choice(weather_conditions)
        temp = random.choice(temperatures)
        
        result = f"{city}的天气: {weather}, 温度: {temp}°C"
        logger.info(result)
        return result
    except Exception as e:
        logger.error(f"获取天气失败: {str(e)}")
        raise

def create_backup(folder_path="./", backup_name=None):
    """创建备份示例任务"""
    if backup_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
    
    # 在实际应用中，这里应该实现真正的备份逻辑
    backup_path = os.path.join("logs", backup_name + ".txt")
    
    # 简单地创建一个标记文件表示备份
    with open(backup_path, 'w') as f:
        f.write(f"模拟备份 {folder_path} 在 {datetime.now().isoformat()}")
    
    logger.info(f"创建备份: {backup_path}")
    return backup_path

def long_running_task(duration=10):
    """模拟长时间运行的任务"""
    logger.info(f"开始长时间运行任务，将持续 {duration} 秒")
    
    start_time = time.time()
    # 模拟任务处理
    for i in range(duration):
        # 每秒记录一次进度
        if i > 0:
            time.sleep(1)
        progress = (i + 1) / duration * 100
        logger.info(f"长时间任务进度: {progress:.1f}%")
    
    elapsed = time.time() - start_time
    result = f"长时间任务完成，实际耗时: {elapsed:.2f} 秒"
    logger.info(result)
    return result

def data_cleanup(max_age_days=30, path="./logs"):
    """清理旧数据的示例任务"""
    logger.info(f"开始清理 {path} 中超过 {max_age_days} 天的文件")
    
    now = datetime.now()
    cleanup_count = 0
    
    # 在实际应用中，这里应该实现真正的文件清理逻辑
    # 这里只是模拟
    cleanup_count = random.randint(0, 10)
    
    result = f"清理了 {cleanup_count} 个旧文件"
    logger.info(result)
    return result 