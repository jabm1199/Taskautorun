#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
启动脚本 - 自动化定时任务执行系统
"""

import os
import sys
import webbrowser
import time

def ensure_directories():
    """确保必要的目录存在"""
    directories = ['logs', 'static/css', 'static/js', 'templates']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def start_application():
    """启动应用程序"""
    print("=" * 50)
    print("自动化定时任务执行系统 - 启动器")
    print("=" * 50)
    
    # 确保目录存在
    ensure_directories()
    
    # 检查是否安装了必要的依赖
    try:
        import flask
        import flask_restful
        import apscheduler
    except ImportError:
        print("缺少必要的依赖，正在安装...")
        os.system(f"{sys.executable} -m pip install -r requirements.txt")
    
    # 启动应用
    print("\n正在启动应用服务器...")
    
    # 启动Web浏览器
    def open_browser():
        """在浏览器中打开应用"""
        time.sleep(2)  # 等待服务器启动
        webbrowser.open('http://localhost:5000')
        print("已在浏览器中打开应用，如未自动打开，请访问: http://localhost:5000")
    
    # 在新线程中打开浏览器，避免阻塞主线程
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # 启动Flask应用
    from app import app
    app.run(debug=True, use_reloader=False)

if __name__ == "__main__":
    start_application() 