from flask import Flask, render_template
from flask_restful import Api
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
import os
import logging
from logging.handlers import RotatingFileHandler

# 确保logs目录存在
os.makedirs('logs', exist_ok=True)

# 确保静态资源目录存在
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# 配置日志
logging.basicConfig(level=logging.INFO)

# 应用日志
app_handler = RotatingFileHandler('logs/app.log', maxBytes=10000, backupCount=3, encoding='utf-8')
app_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app_handler.setLevel(logging.INFO)

# 任务日志
task_logger = logging.getLogger('task_logger')
task_logger.setLevel(logging.INFO)
task_handler = RotatingFileHandler('logs/tasks.log', maxBytes=10000, backupCount=3, encoding='utf-8')
task_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
task_logger.addHandler(task_handler)

# 创建应用
app = Flask(__name__)
api = Api(app)
app.logger.addHandler(app_handler)

# 初始化调度器
scheduler = BackgroundScheduler(
    jobstores={
        'default': MemoryJobStore()
    }
)
scheduler.start()

# 导入路由
from routes import register_routes

register_routes(api, scheduler)

# 添加前端页面路由
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True) 