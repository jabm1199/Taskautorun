import requests
import json
import time
from datetime import datetime, timedelta

# 配置
BASE_URL = 'http://localhost:5000/api'

def test_workflow():
    """测试完整的工作流程：创建、启动、执行、停止任务"""
    print("开始测试定时任务API...")
    
    # 1. 创建任务
    print("\n1. 创建新任务")
    task_data = {
        "name": "测试任务",
        "function": "hello_world",
        "args": {"name": "测试用户"}
    }
    
    response = requests.post(f"{BASE_URL}/tasks", json=task_data)
    if response.status_code != 200:
        print(f"创建任务失败: {response.text}")
        return
    
    task_id = response.json().get('id')
    print(f"任务已创建，ID: {task_id}")
    
    # 2. 获取任务详情
    print("\n2. 获取任务详情")
    response = requests.get(f"{BASE_URL}/tasks/{task_id}")
    if response.status_code == 200:
        print(f"任务详情: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"获取任务详情失败: {response.text}")
    
    # 3. 启动任务（每30秒执行一次）
    print("\n3. 启动任务（每30秒执行一次）")
    start_config = {
        "interval": 30,
        "start_time": datetime.now().isoformat(),
        "end_time": (datetime.now() + timedelta(minutes=10)).isoformat()
    }
    
    response = requests.post(f"{BASE_URL}/tasks/{task_id}/start", json=start_config)
    if response.status_code == 200:
        print("任务已启动")
        print(f"启动配置: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"启动任务失败: {response.text}")
        return
    
    # 4. 立即执行任务
    print("\n4. 立即执行任务")
    response = requests.post(f"{BASE_URL}/tasks/{task_id}/execute")
    if response.status_code == 200:
        print(f"任务执行结果: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"执行任务失败: {response.text}")
    
    # 等待几秒钟，让调度器有机会运行任务
    print("\n等待5秒钟...")
    time.sleep(5)
    
    # 5. 再次获取任务详情，查看运行情况
    print("\n5. 再次获取任务详情")
    response = requests.get(f"{BASE_URL}/tasks/{task_id}")
    if response.status_code == 200:
        print(f"任务详情: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"获取任务详情失败: {response.text}")
    
    # 6. 停止任务
    print("\n6. 停止任务")
    response = requests.post(f"{BASE_URL}/tasks/{task_id}/stop")
    if response.status_code == 200:
        print("任务已停止")
        print(f"任务状态: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"停止任务失败: {response.text}")
    
    # 7. 删除任务
    print("\n7. 删除任务")
    response = requests.delete(f"{BASE_URL}/tasks/{task_id}")
    if response.status_code == 200:
        print("任务已删除")
    else:
        print(f"删除任务失败: {response.text}")
    
    print("\n测试完成!")

def test_list_tasks():
    """测试获取所有任务列表"""
    print("\n获取所有任务列表")
    response = requests.get(f"{BASE_URL}/tasks")
    if response.status_code == 200:
        tasks = response.json().get('tasks', [])
        print(f"共有 {len(tasks)} 个任务")
        for task in tasks:
            print(f"- {task['name']} (ID: {task['id']}, 状态: {task['status']})")
    else:
        print(f"获取任务列表失败: {response.text}")

def test_cron_task():
    """测试使用Cron表达式的任务"""
    print("\n测试Cron表达式任务")
    
    # 创建任务
    task_data = {
        "name": "Cron测试任务",
        "function": "random_number",
        "args": {"min_val": 1, "max_val": 1000}
    }
    
    response = requests.post(f"{BASE_URL}/tasks", json=task_data)
    if response.status_code != 200:
        print(f"创建任务失败: {response.text}")
        return
    
    task_id = response.json().get('id')
    print(f"任务已创建，ID: {task_id}")
    
    # 使用Cron表达式启动（每分钟执行一次）
    cron_config = {
        "cron": "* * * * *",
        "start_time": datetime.now().isoformat(),
        "end_time": (datetime.now() + timedelta(minutes=5)).isoformat()
    }
    
    response = requests.post(f"{BASE_URL}/tasks/{task_id}/start", json=cron_config)
    if response.status_code == 200:
        print("Cron任务已启动")
        print(f"启动配置: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"启动任务失败: {response.text}")
        return
    
    # 立即执行一次
    response = requests.post(f"{BASE_URL}/tasks/{task_id}/execute")
    if response.status_code == 200:
        print(f"任务执行结果: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    # 停止任务
    print("停止Cron任务")
    response = requests.post(f"{BASE_URL}/tasks/{task_id}/stop")
    if response.status_code == 200:
        print("任务已停止")
    else:
        print(f"停止任务失败: {response.text}")
    
    # 删除任务
    requests.delete(f"{BASE_URL}/tasks/{task_id}")

if __name__ == "__main__":
    # 测试所有API功能
    test_workflow()
    
    # 测试获取任务列表
    test_list_tasks()
    
    # 测试Cron表达式任务
    test_cron_task() 