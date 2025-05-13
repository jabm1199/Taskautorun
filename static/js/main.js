// API基础URL
const API_BASE_URL = '/api';

// 当前任务ID和名称（用于日志查看）
let currentTaskId = null;
let currentTaskName = null;

// DOM元素加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化加载任务列表
    loadTasks();
    
    // 加载可用的任务函数
    loadFunctions();
    
    // 刷新按钮点击事件
    document.getElementById('refreshBtn').addEventListener('click', loadTasks);
    
    // 创建任务按钮点击事件
    document.getElementById('createTaskBtn').addEventListener('click', createTask);
    
    // 启动任务按钮点击事件
    document.getElementById('startTaskBtn').addEventListener('click', startTask);
    
    // 刷新日志按钮点击事件
    document.getElementById('refreshLogsBtn').addEventListener('click', refreshLogs);
    
    // 日志参数变化事件
    document.getElementById('logDays').addEventListener('change', refreshLogs);
    document.getElementById('logLines').addEventListener('change', refreshLogs);
    
    // 切换调度类型事件
    document.querySelectorAll('input[name="schedulerType"]').forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'interval') {
                document.getElementById('intervalSection').style.display = 'block';
                document.getElementById('cronSection').style.display = 'none';
            } else {
                document.getElementById('intervalSection').style.display = 'none';
                document.getElementById('cronSection').style.display = 'block';
            }
        });
    });
});

// 加载可用的任务函数
function loadFunctions() {
    fetch(`${API_BASE_URL}/functions`)
        .then(response => response.json())
        .then(data => {
            const taskFunction = document.getElementById('taskFunction');
            
            if (!data.functions || data.functions.length === 0) {
                return;
            }
            
            // 清空现有选项（保留第一个默认选项）
            const defaultOption = taskFunction.options[0];
            taskFunction.innerHTML = '';
            taskFunction.appendChild(defaultOption);
            
            // 添加函数选项
            data.functions.forEach(func => {
                const option = document.createElement('option');
                option.value = func.name;
                
                // 提取简短描述（第一行）
                const shortDesc = func.description.split('\n')[0];
                
                option.textContent = `${func.name} - ${shortDesc}`;
                
                // 添加完整信息作为自定义属性
                option.setAttribute('data-description', func.description);
                option.setAttribute('data-parameters', JSON.stringify(func.parameters));
                
                taskFunction.appendChild(option);
            });
            
            // 添加任务函数选择事件：当选择函数时，自动生成示例参数JSON
            taskFunction.addEventListener('change', function() {
                const selectedOption = this.options[this.selectedIndex];
                if (selectedOption.value) {
                    const parametersAttr = selectedOption.getAttribute('data-parameters');
                    if (parametersAttr) {
                        try {
                            const parameters = JSON.parse(parametersAttr);
                            if (parameters.length > 0) {
                                const exampleArgs = {};
                                parameters.forEach(param => {
                                    if ('default' in param) {
                                        exampleArgs[param.name] = param.default;
                                    }
                                });
                                
                                // 如果有默认参数，设置到文本域
                                if (Object.keys(exampleArgs).length > 0) {
                                    document.getElementById('taskArgs').value = JSON.stringify(exampleArgs, null, 2);
                                }
                            }
                        } catch (e) {
                            console.error('解析函数参数失败', e);
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading functions:', error);
            showError('加载任务函数列表失败');
        });
}

// 加载任务列表
function loadTasks() {
    fetch(`${API_BASE_URL}/tasks`)
        .then(response => response.json())
        .then(data => {
            const taskList = document.getElementById('taskList');
            
            if (!data.tasks || data.tasks.length === 0) {
                taskList.innerHTML = '<tr><td colspan="7" class="text-center">暂无任务数据</td></tr>';
                return;
            }
            
            let html = '';
            data.tasks.forEach(task => {
                html += `
                <tr>
                    <td>${escapeHtml(task.name)}</td>
                    <td>${escapeHtml(task.function)}</td>
                    <td><span class="task-status status-${task.status}">${getStatusText(task.status)}</span></td>
                    <td>${formatDateTime(task.last_run)}</td>
                    <td>${formatDateTime(task.next_run)}</td>
                    <td>${task.run_count}</td>
                    <td>
                        <div class="action-group">
                            <button class="btn btn-sm btn-info btn-action" onclick="viewTaskDetail('${task.id}')">
                                <i class="fas fa-info-circle"></i> 详情
                            </button>
                            <button class="btn btn-sm btn-secondary btn-action" onclick="viewTaskLogs('${task.id}', '${escapeHtml(task.name)}')">
                                <i class="fas fa-list-alt"></i> 日志
                            </button>
                            ${task.status !== 'running' ? 
                            `<button class="btn btn-sm btn-success btn-action" onclick="openStartTaskModal('${task.id}')">
                                <i class="fas fa-play"></i> 启动
                            </button>` : ''}
                            ${task.status === 'running' ? 
                            `<button class="btn btn-sm btn-warning btn-action" onclick="stopTask('${task.id}')">
                                <i class="fas fa-stop"></i> 停止
                            </button>` : ''}
                            <button class="btn btn-sm btn-primary btn-action" onclick="executeTask('${task.id}')">
                                <i class="fas fa-bolt"></i> 执行
                            </button>
                            <button class="btn btn-sm btn-danger btn-action" onclick="deleteTask('${task.id}')">
                                <i class="fas fa-trash"></i> 删除
                            </button>
                        </div>
                    </td>
                </tr>
                `;
            });
            
            taskList.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading tasks:', error);
            showError('加载任务失败');
        });
}

// 查看任务详情
function viewTaskDetail(taskId) {
    fetch(`${API_BASE_URL}/tasks/${taskId}`)
        .then(response => response.json())
        .then(task => {
            // 检查是否有错误
            if (task.error) {
                showError(task.error);
                return;
            }
            
            // 构建详情HTML
            let html = `
            <table class="detail-table">
                <tr>
                    <th>任务ID</th>
                    <td>${escapeHtml(task.id)}</td>
                </tr>
                <tr>
                    <th>任务名称</th>
                    <td>${escapeHtml(task.name)}</td>
                </tr>
                <tr>
                    <th>任务函数</th>
                    <td>${escapeHtml(task.function)}</td>
                </tr>
                <tr>
                    <th>状态</th>
                    <td><span class="task-status status-${task.status}">${getStatusText(task.status)}</span></td>
                </tr>
                <tr>
                    <th>创建时间</th>
                    <td>${formatDateTime(task.created_at)}</td>
                </tr>
                <tr>
                    <th>上次运行</th>
                    <td>${formatDateTime(task.last_run)}</td>
                </tr>
                <tr>
                    <th>下次运行</th>
                    <td>${formatDateTime(task.next_run)}</td>
                </tr>
                <tr>
                    <th>运行次数</th>
                    <td>${task.run_count}</td>
                </tr>
            `;
            
            // 如果有间隔配置
            if (task.interval) {
                html += `
                <tr>
                    <th>执行间隔（秒）</th>
                    <td>${task.interval}</td>
                </tr>
                `;
            }
            
            // 如果有Cron配置
            if (task.cron) {
                html += `
                <tr>
                    <th>Cron表达式</th>
                    <td>${escapeHtml(task.cron)}</td>
                </tr>
                `;
            }
            
            // 如果有开始时间
            if (task.start_time) {
                html += `
                <tr>
                    <th>开始时间</th>
                    <td>${formatDateTime(task.start_time)}</td>
                </tr>
                `;
            }
            
            // 如果有结束时间
            if (task.end_time) {
                html += `
                <tr>
                    <th>结束时间</th>
                    <td>${formatDateTime(task.end_time)}</td>
                </tr>
                `;
            }
            
            // 函数参数
            html += `
                <tr>
                    <th>函数参数</th>
                    <td><pre class="json">${JSON.stringify(task.args, null, 2)}</pre></td>
                </tr>
            </table>
            `;
            
            document.getElementById('taskDetailContent').innerHTML = html;
            
            // 显示详情模态框
            const modal = new bootstrap.Modal(document.getElementById('taskDetailModal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error viewing task details:', error);
            showError('加载任务详情失败');
        });
}

// 查看任务日志
function viewTaskLogs(taskId, taskName) {
    // 保存当前任务信息
    currentTaskId = taskId;
    currentTaskName = taskName;
    
    // 设置模态框标题
    document.getElementById('taskLogsModalLabel').textContent = `任务日志: ${taskName}`;
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('taskLogsModal'));
    modal.show();
    
    // 加载日志
    loadTaskLogs();
}

// 查看所有日志
function viewAllLogs() {
    // 清除当前任务信息
    currentTaskId = null;
    currentTaskName = null;
    
    // 设置模态框标题
    document.getElementById('taskLogsModalLabel').textContent = '全局任务日志';
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('taskLogsModal'));
    modal.show();
    
    // 加载日志
    loadTaskLogs();
}

// 刷新日志
function refreshLogs() {
    loadTaskLogs();
}

// 加载任务日志
function loadTaskLogs() {
    const days = document.getElementById('logDays').value;
    const lines = document.getElementById('logLines').value;
    
    let url = `${API_BASE_URL}/logs`;
    if (currentTaskId) {
        url += `/${currentTaskId}`;
    }
    url += `?days=${days}&lines=${lines}`;
    
    // 显示加载中
    document.getElementById('logsList').innerHTML = '<tr><td colspan="3" class="text-center">加载中...</td></tr>';
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP错误 ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const logsList = document.getElementById('logsList');
            
            if (data.error) {
                logsList.innerHTML = `<tr><td colspan="3" class="text-center text-danger">错误: ${escapeHtml(data.error)}</td></tr>`;
                return;
            }
            
            if (!data.logs || data.logs.length === 0) {
                logsList.innerHTML = '<tr><td colspan="3" class="text-center">暂无日志数据</td></tr>';
                return;
            }
            
            let html = '';
            data.logs.forEach(log => {
                html += `
                <tr>
                    <td>${log.timestamp}</td>
                    <td><span class="log-level log-level-${log.level}">${log.level}</span></td>
                    <td class="log-message">${escapeHtml(log.message)}</td>
                </tr>
                `;
            });
            
            logsList.innerHTML = html;
            
            // 滚动到底部
            const logContainer = document.querySelector('.log-container');
            logContainer.scrollTop = logContainer.scrollHeight;
        })
        .catch(error => {
            console.error('Error loading logs:', error);
            const errorMessage = error.message || '未知错误';
            const diagnosticMessage = getLogDiagnosticMessage(errorMessage);
            
            document.getElementById('logsList').innerHTML = `
                <tr><td colspan="3" class="text-center text-danger">加载日志失败: ${escapeHtml(errorMessage)}</td></tr>
                <tr><td colspan="3" class="text-center">${diagnosticMessage}</td></tr>
            `;
        });
}

// 获取日志错误的诊断信息
function getLogDiagnosticMessage(errorMessage) {
    if (errorMessage.includes('UnicodeDecodeError') || errorMessage.includes('invalid')) {
        return `
            <div class="alert alert-info mt-2">
                <h5>可能的编码问题</h5>
                <p>系统检测到日志文件可能存在编码问题。这通常发生在：</p>
                <ul>
                    <li>日志文件包含非UTF-8编码的中文字符</li>
                    <li>日志文件由不同编码格式的程序写入</li>
                </ul>
                <p>系统已尝试自动修复此问题。请尝试重新启动应用或刷新页面。如果问题持续存在，请联系管理员检查日志文件编码。</p>
            </div>
        `;
    }
    return '';
}

// 创建新任务
function createTask() {
    const name = document.getElementById('taskName').value.trim();
    const functionName = document.getElementById('taskFunction').value;
    let args = {};
    
    // 解析JSON参数
    const argsText = document.getElementById('taskArgs').value.trim();
    if (argsText) {
        try {
            args = JSON.parse(argsText);
        } catch (e) {
            showError('函数参数格式不正确，请输入有效的JSON格式');
            return;
        }
    }
    
    // 验证输入
    if (!name) {
        showError('请输入任务名称');
        return;
    }
    
    if (!functionName) {
        showError('请选择任务函数');
        return;
    }
    
    // 构建请求数据
    const taskData = {
        name: name,
        function: functionName,
        args: args
    };
    
    // 发送API请求
    fetch(`${API_BASE_URL}/tasks`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(taskData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('createTaskModal'));
        modal.hide();
        
        // 重置表单
        document.getElementById('createTaskForm').reset();
        
        // 提示成功
        showSuccess('任务创建成功');
        
        // 刷新任务列表
        loadTasks();
    })
    .catch(error => {
        console.error('Error creating task:', error);
        showError('创建任务失败');
    });
}

// 打开启动任务模态框
function openStartTaskModal(taskId) {
    // 重置表单
    document.getElementById('startTaskForm').reset();
    document.getElementById('intervalSection').style.display = 'block';
    document.getElementById('cronSection').style.display = 'none';
    
    // 设置任务ID
    document.getElementById('startTaskId').value = taskId;
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('startTaskModal'));
    modal.show();
}

// 启动任务
function startTask() {
    const taskId = document.getElementById('startTaskId').value;
    const schedulerType = document.querySelector('input[name="schedulerType"]:checked').value;
    
    // 构建配置对象
    const config = {};
    
    // 添加开始和结束时间（如果有）
    const startTime = document.getElementById('startTime').value;
    if (startTime) {
        config.start_time = new Date(startTime).toISOString();
    }
    
    const endTime = document.getElementById('endTime').value;
    if (endTime) {
        config.end_time = new Date(endTime).toISOString();
    }
    
    // 根据调度类型添加不同的配置
    if (schedulerType === 'interval') {
        const interval = parseInt(document.getElementById('interval').value);
        if (isNaN(interval) || interval <= 0) {
            showError('请输入有效的执行间隔');
            return;
        }
        config.interval = interval;
    } else {
        const cronExpression = document.getElementById('cronExpression').value.trim();
        if (!cronExpression) {
            showError('请输入Cron表达式');
            return;
        }
        config.cron = cronExpression;
    }
    
    // 发送API请求
    fetch(`${API_BASE_URL}/tasks/${taskId}/start`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('startTaskModal'));
        modal.hide();
        
        // 提示成功
        showSuccess('任务启动成功');
        
        // 刷新任务列表
        loadTasks();
    })
    .catch(error => {
        console.error('Error starting task:', error);
        showError('启动任务失败');
    });
}

// 停止任务
function stopTask(taskId) {
    if (!confirm('确定要停止此任务吗？')) {
        return;
    }
    
    fetch(`${API_BASE_URL}/tasks/${taskId}/stop`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        showSuccess('任务已停止');
        loadTasks();
    })
    .catch(error => {
        console.error('Error stopping task:', error);
        showError('停止任务失败');
    });
}

// 立即执行任务
function executeTask(taskId) {
    fetch(`${API_BASE_URL}/tasks/${taskId}/execute`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        showSuccess('任务执行成功: ' + data.result);
        
        // 短暂延迟后刷新列表，以显示最新的运行状态
        setTimeout(loadTasks, 1000);
    })
    .catch(error => {
        console.error('Error executing task:', error);
        showError('执行任务失败');
    });
}

// 删除任务
function deleteTask(taskId) {
    if (!confirm('确定要删除此任务吗？此操作不可恢复。')) {
        return;
    }
    
    fetch(`${API_BASE_URL}/tasks/${taskId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        showSuccess('任务已删除');
        loadTasks();
    })
    .catch(error => {
        console.error('Error deleting task:', error);
        showError('删除任务失败');
    });
}

// 成功提示
function showSuccess(message) {
    Swal.fire({
        icon: 'success',
        title: '成功',
        text: message,
        timer: 2000,
        showConfirmButton: false
    });
}

// 错误提示
function showError(message) {
    Swal.fire({
        icon: 'error',
        title: '错误',
        text: message
    });
}

// 格式化日期时间
function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return '—';
    
    const date = new Date(dateTimeStr);
    if (isNaN(date.getTime())) return dateTimeStr;
    
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'created': '已创建',
        'running': '运行中',
        'stopped': '已停止',
        'error': '错误'
    };
    
    return statusMap[status] || status;
}

// HTML转义，防止XSS攻击
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
} 