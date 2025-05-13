# Python自动化定时任务执行系统

这是一个基于Flask和APScheduler的自动化定时任务执行系统，允许通过API接口和Web界面创建、管理和执行定时任务。

## 功能特点

1. **定时任务创建**：通过API接口或Web界面创建新的定时任务
2. **定时任务控制**：开启、停止定时任务，设置运行周期
3. **立即执行**：可以立即执行指定的任务
4. **任务状态查询**：查看任务的状态和详细信息
5. **日志记录**：详细记录任务执行情况，存储在logs目录
6. **Web界面管理**：通过友好的Web界面管理所有任务
7. **日志查看**：在Web界面直接查看任务执行日志，支持按任务筛选和时间范围筛选

## 安装

1. 克隆此仓库
2. 安装依赖包：

```bash
pip install -r requirements.txt
```

## 使用方法

### 使用启动脚本（推荐）

执行以下命令启动应用：

```bash
python start.py
```

启动脚本会自动：
1. 检查并创建必要的目录
2. 安装所需依赖（如果缺少）
3. 启动应用服务器
4. 在浏览器中打开应用界面

### 手动启动服务

如果您不想使用启动脚本，也可以手动启动：

```bash
python app.py
```

服务将在默认的`http://localhost:5000`上运行。

### Web界面使用

访问 `http://localhost:5000` 即可打开Web管理界面。

通过Web界面，您可以：

- 查看所有任务及其状态
- 创建新任务
- 查看任务详情
- 查看任务执行日志
- 启动/停止任务
- 立即执行任务
- 删除任务

#### 日志查看功能

系统提供了强大的日志查看功能：

1. **查看特定任务日志**：在任务列表中点击"日志"按钮，可以查看该任务的执行日志
2. **查看全局日志**：点击界面顶部的"查看全局日志"按钮，可以查看所有任务的日志
3. **日志筛选**：可以指定查看最近的天数（1天、3天、7天、30天或全部）
4. **日志条数限制**：可以限制显示的日志行数（100行、500行、1000行或全部）
5. **实时更新**：点击"刷新日志"按钮，可以获取最新的日志内容

### API接口

#### 获取所有任务

```
GET /api/tasks
```

#### 创建新任务

```
POST /api/tasks
```

参数：
- `name`: 任务名称（必填）
- `function`: 要执行的函数名（必填）
- `args`: 函数参数（可选，JSON对象）

示例：
```json
{
  "name": "问候任务",
  "function": "hello_world",
  "args": {
    "name": "张三"
  }
}
```

#### 获取任务详情

```
GET /api/tasks/<task_id>
```

#### 更新任务

```
PUT /api/tasks/<task_id>
```

参数（均为可选）：
- `start_time`: 开始时间
- `end_time`: 结束时间
- `interval`: 间隔（秒）
- `cron`: Cron表达式

#### 删除任务

```
DELETE /api/tasks/<task_id>
```

#### 启动任务

```
POST /api/tasks/<task_id>/start
```

参数（至少需要一个）：
- `start_time`: 开始时间（ISO格式：YYYY-MM-DD HH:MM:SS）
- `end_time`: 结束时间（ISO格式：YYYY-MM-DD HH:MM:SS）
- `interval`: 运行间隔（秒）
- `cron`: Cron表达式（例如："*/5 * * * *"）

#### 停止任务

```
POST /api/tasks/<task_id>/stop
```

#### 立即执行任务

```
POST /api/tasks/<task_id>/execute
```

#### 获取任务日志

```
GET /api/logs/<task_id>
```

参数（均为可选）：
- `days`: 获取最近几天的日志，默认1天，0表示全部
- `lines`: 获取的日志行数，默认100行，0表示全部

#### 获取全局日志

```
GET /api/logs
```

参数同上。

## 添加自定义任务

在`tasks.py`中添加您自己的函数，然后可以通过API或Web界面调度这些函数。

例如，添加一个新函数：

```python
def my_custom_task(param1="默认值", param2=100):
    """我的自定义任务"""
    result = f"执行自定义任务，参数：{param1}, {param2}"
    logger.info(result)
    return result
```

添加函数后，您可以在Web界面的"任务函数"下拉框中选择这个函数，或通过API创建使用该函数的任务。

## 日志

任务执行日志保存在`logs/tasks.log`文件中。
应用程序日志保存在`logs/app.log`文件中。

## 系统截图

![任务列表](screenshots/task_list.png)
*任务列表界面*

![创建任务](screenshots/create_task.png)
*创建新任务*

![任务详情](screenshots/task_detail.png)
*查看任务详情*

![任务日志](screenshots/task_logs.png)
*查看任务执行日志*

## 示例

### 创建一个每5分钟执行一次的天气查询任务

```bash
curl -X POST http://localhost:5000/api/tasks -H "Content-Type: application/json" -d '{"name": "天气查询", "function": "fetch_weather", "args": {"city": "上海"}}'
```

获取返回的任务ID，然后启动任务：

```bash
curl -X POST http://localhost:5000/api/tasks/<task_id>/start -H "Content-Type: application/json" -d '{"cron": "*/5 * * * *"}'
```

### 立即执行一个任务

```bash
curl -X POST http://localhost:5000/api/tasks/<task_id>/execute
```

### 查看任务日志

```bash
curl http://localhost:5000/api/logs/<task_id>?days=1&lines=100
``` 