// API基础URL
const API_BASE_URL = '/api';

// 全局变量，用于跟踪当前选中的任务ID和名称
let currentTaskId = null;
let currentTaskName = null;

// 全局变量，用于跟踪当前选中的任务组ID和名称
let currentTaskGroupId = null;
let currentTaskGroupName = null;

// DOM元素加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化加载任务列表
    loadTasks();
    
    // 初始化加载任务组列表
    loadTaskGroups();
    
    // 加载可用的任务函数
    loadFunctions();
    
    // 刷新按钮点击事件
    document.getElementById('refreshBtn').addEventListener('click', loadTasks);
    
    // 刷新任务组按钮点击事件
    document.getElementById('refreshTaskGroupsBtn').addEventListener('click', loadTaskGroups);
    
    // 创建任务按钮点击事件
    document.getElementById('createTaskBtn').addEventListener('click', createTask);
    
    // 创建任务组按钮点击事件
    document.getElementById('createTaskGroupBtn').addEventListener('click', createTaskGroup);
    
    // 启动任务按钮点击事件
    document.getElementById('startTaskBtn').addEventListener('click', startTask);
    
    // 启动任务组按钮点击事件
    document.getElementById('startTaskGroupBtn').addEventListener('click', startTaskGroup);
    
    // 添加任务到任务组按钮点击事件
    document.getElementById('addTaskToGroupBtn').addEventListener('click', function() {
        toggleTaskSelectionSection(true);
        loadAvailableTasks();
    });
    
    // 刷新日志按钮点击事件
    document.getElementById('refreshLogsBtn').addEventListener('click', refreshLogs);
    
    // 清除日志按钮点击事件
    document.getElementById('clearLogsBtn').addEventListener('click', clearLogs);
    
    // 日志参数变化事件
    document.getElementById('logDays').addEventListener('change', refreshLogs);
    document.getElementById('logLines').addEventListener('change', refreshLogs);
    
    // 切换调度类型事件 - 任务
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
    
    // 切换调度类型事件 - 任务组
    document.querySelectorAll('input[name="groupSchedulerType"]').forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'interval') {
                document.getElementById('groupIntervalSection').style.display = 'block';
                document.getElementById('groupCronSection').style.display = 'none';
            } else {
                document.getElementById('groupIntervalSection').style.display = 'none';
                document.getElementById('groupCronSection').style.display = 'block';
            }
        });
    });
});

// 任务组相关功能
// ===================

// 加载任务组列表
function loadTaskGroups() {
    fetch(`${API_BASE_URL}/task-groups`)
        .then(response => response.json())
        .then(data => {
            const taskGroupList = document.getElementById('taskGroupList');
            
            if (!data.task_groups || data.task_groups.length === 0) {
                taskGroupList.innerHTML = '<tr><td colspan="7" class="text-center">暂无任务组数据</td></tr>';
                return;
            }
            
            let html = '';
            data.task_groups.forEach(group => {
                html += `
                <tr data-id="${group.id}">
                    <td>${escapeHtml(group.name)}</td>
                    <td>${group.task_ids.length}</td>
                    <td><span class="task-status status-${group.status}">${getGroupStatusText(group.status)}</span></td>
                    <td>${formatDateTime(group.last_run)}</td>
                    <td>${formatDateTime(group.next_run)}</td>
                    <td>${group.run_count}</td>
                    <td>
                        <div class="action-group">
                            <button class="btn btn-sm btn-info btn-action" onclick="viewTaskGroupDetail('${group.id}')">
                                <i class="fas fa-info-circle"></i> 详情
                            </button>
                            <button class="btn btn-sm btn-secondary btn-action" onclick="viewTaskLogs('${group.id}', '${escapeHtml(group.name)}')">
                                <i class="fas fa-list-alt"></i> 日志
                            </button>
                            ${group.status !== 'running' ? 
                            `<button class="btn btn-sm btn-success btn-action" onclick="openStartTaskGroupModal('${group.id}')">
                                <i class="fas fa-play"></i> 启动
                            </button>` : ''}
                            ${group.status === 'running' ? 
                            `<button class="btn btn-sm btn-warning btn-action" onclick="stopTaskGroup('${group.id}')">
                                <i class="fas fa-stop"></i> 停止
                            </button>` : ''}
                            <button class="btn btn-sm btn-primary btn-action" onclick="executeTaskGroup('${group.id}')">
                                <i class="fas fa-bolt"></i> 执行
                            </button>
                            <button class="btn btn-sm btn-danger btn-action" onclick="deleteTaskGroup('${group.id}')">
                                <i class="fas fa-trash"></i> 删除
                            </button>
                        </div>
                    </td>
                </tr>
                `;
            });
            
            taskGroupList.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading task groups:', error);
            showError('加载任务组失败');
        });
}

// 创建新任务组
function createTaskGroup() {
    const name = document.getElementById('taskGroupName').value.trim();
    
    // 验证输入
    if (!name) {
        showError('请输入任务组名称');
        return;
    }
    
    // 构建请求数据
    const taskGroupData = {
        name: name,
        task_ids: []
    };
    
    // 发送API请求
    fetch(`${API_BASE_URL}/task-groups`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(taskGroupData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('createTaskGroupModal'));
        modal.hide();
        
        // 重置表单
        document.getElementById('createTaskGroupForm').reset();
        
        // 提示成功
        showSuccess('任务组创建成功');
        
        // 刷新任务组列表
        loadTaskGroups();
        
        // 打开任务组详情，以便添加任务
        viewTaskGroupDetail(data.id);
    })
    .catch(error => {
        console.error('Error creating task group:', error);
        showError('创建任务组失败');
    });
}

// 查看任务组详情
function viewTaskGroupDetail(groupId) {
    currentTaskGroupId = groupId;
    
    fetch(`${API_BASE_URL}/task-groups/${groupId}`)
        .then(response => response.json())
        .then(group => {
            // 检查是否有错误
            if (group.error) {
                showError(group.error);
                return;
            }
            
            currentTaskGroupName = group.name;
            
            // 构建详情HTML
            let html = `
            <table class="detail-table">
                <tr>
                    <th>任务组ID</th>
                    <td>${escapeHtml(group.id)}</td>
                </tr>
                <tr>
                    <th>任务组名称</th>
                    <td>${escapeHtml(group.name)}</td>
                </tr>
                <tr>
                    <th>状态</th>
                    <td><span class="task-status status-${group.status}">${getGroupStatusText(group.status)}</span></td>
                </tr>
                <tr>
                    <th>创建时间</th>
                    <td>${formatDateTime(group.created_at)}</td>
                </tr>
                <tr>
                    <th>上次运行</th>
                    <td>${formatDateTime(group.last_run)}</td>
                </tr>
                <tr>
                    <th>下次运行</th>
                    <td>${formatDateTime(group.next_run)}</td>
                </tr>
                <tr>
                    <th>运行次数</th>
                    <td>${group.run_count}</td>
                </tr>
                <tr>
                    <th>包含任务数</th>
                    <td>${group.task_ids.length}</td>
                </tr>
            </table>
            
            <div class="mt-3 d-flex gap-2">
                ${group.status !== 'running' ? 
                `<button class="btn btn-success" onclick="openStartTaskGroupModal('${group.id}')">
                    <i class="fas fa-play"></i> 启动任务组
                </button>
                <button class="btn btn-primary" onclick="executeTaskGroupFromDetail('${group.id}')">
                    <i class="fas fa-bolt"></i> 立即执行
                </button>` : ''}
                
                ${group.status === 'running' ? 
                `<button class="btn btn-warning" onclick="stopTaskGroupFromDetail('${group.id}')">
                    <i class="fas fa-stop"></i> 停止任务组
                </button>` : ''}
                
                <button class="btn btn-secondary" onclick="viewTaskLogs('${group.id}', '${escapeHtml(group.name)}')">
                    <i class="fas fa-list-alt"></i> 查看日志
                </button>
            </div>
            `;
            
            document.getElementById('taskGroupDetailContent').innerHTML = html;
            
            // 加载任务组中的任务列表
            loadTasksInGroup(group.task_ids);
            
            // 隐藏任务选择区域
            toggleTaskSelectionSection(false);
            
            // 显示详情模态框
            const modal = new bootstrap.Modal(document.getElementById('taskGroupDetailModal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error viewing task group details:', error);
            showError('加载任务组详情失败');
        });
}

// 从详情页面执行任务组
function executeTaskGroupFromDetail(groupId) {
    // 隐藏详情页面
    const modal = bootstrap.Modal.getInstance(document.getElementById('taskGroupDetailModal'));
    modal.hide();
    
    // 执行任务组
    fetch(`${API_BASE_URL}/task-groups/${groupId}/execute`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // 首先更新UI状态
        if (data.task_group) {
            updateTaskGroupStatusInUI(data.task_group);
        }
        
        // 检查任务组执行情况
        if (data.task_group && data.task_group.status === 'error') {
            // 如果任务组状态为错误，显示错误消息
            showError('任务组执行失败，可能原因：任务组中的任务不存在或执行出错');
            // 查看日志以获取详细信息
            setTimeout(() => {
                viewTaskLogs(groupId, data.task_group.name);
            }, 1000);
        } else {
            // 正常显示成功消息
            showSuccess(data.message || '任务组开始执行');
        }
        
        // 短暂延迟后刷新列表
        setTimeout(loadTaskGroups, 1000);
    })
    .catch(error => {
        console.error('Error executing task group:', error);
        showError('执行任务组失败');
    });
}

// 从详情页面停止任务组
function stopTaskGroupFromDetail(groupId) {
    // 隐藏详情页面
    const modal = bootstrap.Modal.getInstance(document.getElementById('taskGroupDetailModal'));
    modal.hide();
    
    // 停止任务组
    stopTaskGroup(groupId);
}

// 加载任务组中的任务列表
function loadTasksInGroup(taskIds) {
    if (!taskIds || taskIds.length === 0) {
        document.getElementById('taskGroupTasksList').innerHTML = '<tr><td colspan="4" class="text-center">任务组中暂无任务</td></tr>';
        return;
    }
    
    // 获取任务详情
    let promises = taskIds.map(taskId => 
        fetch(`${API_BASE_URL}/tasks/${taskId}`)
            .then(response => response.json())
    );
    
    Promise.all(promises)
        .then(tasks => {
            let html = '';
            tasks.forEach((task, index) => {
                if (task.error) {
                    html += `
                    <tr>
                        <td>${index + 1}</td>
                        <td colspan="3" class="text-danger">任务不存在或已被删除</td>
                    </tr>
                    `;
                    return;
                }
                
                html += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${escapeHtml(task.name)}<br><small class="text-muted">ID: ${task.id}</small></td>
                    <td>${escapeHtml(task.function)}</td>
                    <td>
                        <button class="btn btn-sm btn-danger" onclick="removeTaskFromGroup('${task.id}')">
                            <i class="fas fa-trash"></i> 移除
                        </button>
                        <button class="btn btn-sm btn-secondary me-1" onclick="viewTaskLogs('${task.id}', '${escapeHtml(task.name)}')">
                            <i class="fas fa-list-alt"></i> 日志
                        </button>
                        ${index > 0 ? 
                        `<button class="btn btn-sm btn-secondary ms-1" onclick="moveTaskUp('${task.id}')">
                            <i class="fas fa-arrow-up"></i>
                        </button>` : ''}
                        ${index < tasks.length - 1 ? 
                        `<button class="btn btn-sm btn-secondary ms-1" onclick="moveTaskDown('${task.id}')">
                            <i class="fas fa-arrow-down"></i>
                        </button>` : ''}
                    </td>
                </tr>
                `;
            });
            
            document.getElementById('taskGroupTasksList').innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading tasks in group:', error);
            document.getElementById('taskGroupTasksList').innerHTML = '<tr><td colspan="4" class="text-center text-danger">加载任务失败</td></tr>';
        });
}

// 加载可供添加到任务组的任务
function loadAvailableTasks() {
    // 首先获取当前任务组中的任务ID列表
    fetch(`${API_BASE_URL}/task-groups/${currentTaskGroupId}`)
        .then(response => response.json())
        .then(group => {
            const existingTaskIds = group.task_ids || [];
            
            // 然后获取所有任务
            return fetch(`${API_BASE_URL}/tasks`)
                .then(response => response.json())
                .then(data => {
                    const availableTasks = data.tasks.filter(task => !existingTaskIds.includes(task.id));
                    
                    if (availableTasks.length === 0) {
                        document.getElementById('availableTasksList').innerHTML = '<tr><td colspan="3" class="text-center">没有可添加的任务</td></tr>';
                        return;
                    }
                    
                    let html = '';
                    availableTasks.forEach(task => {
                        html += `
                        <tr>
                            <td>${escapeHtml(task.name)}<br><small class="text-muted">ID: ${task.id}</small></td>
                            <td>${escapeHtml(task.function)}</td>
                            <td>
                                <button class="btn btn-sm btn-success" onclick="addTaskToGroup('${task.id}')">
                                    <i class="fas fa-plus"></i> 添加
                                </button>
                            </td>
                        </tr>
                        `;
                    });
                    
                    document.getElementById('availableTasksList').innerHTML = html;
                });
        })
        .catch(error => {
            console.error('Error loading available tasks:', error);
            document.getElementById('availableTasksList').innerHTML = '<tr><td colspan="3" class="text-center text-danger">加载任务失败</td></tr>';
        });
}

// 切换任务选择区域的显示状态
function toggleTaskSelectionSection(show) {
    document.getElementById('taskSelectionSection').style.display = show ? 'block' : 'none';
}

// 添加任务到任务组
function addTaskToGroup(taskId) {
    fetch(`${API_BASE_URL}/task-groups/${currentTaskGroupId}/tasks`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ task_id: taskId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // 刷新任务组中的任务列表
        loadTasksInGroup(data.task_ids);
        
        // 刷新可用任务列表
        loadAvailableTasks();
        
        showSuccess('添加任务成功');
    })
    .catch(error => {
        console.error('Error adding task to group:', error);
        showError('添加任务失败');
    });
}

// 从任务组中移除任务
function removeTaskFromGroup(taskId) {
    if (!confirm('确定要从任务组中移除此任务吗？移除后若执行任务组可能导致错误，请确保更新任务组后再执行。')) {
        return;
    }
    
    fetch(`${API_BASE_URL}/task-groups/${currentTaskGroupId}/tasks`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ task_id: taskId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // 刷新任务组中的任务列表
        loadTasksInGroup(data.task_ids);
        
        // 如果正在显示可用任务，则刷新
        if (document.getElementById('taskSelectionSection').style.display === 'block') {
            loadAvailableTasks();
        }
        
        showSuccess('移除任务成功，任务组已更新');
        
        // 刷新任务组列表以确保UI状态正确
        setTimeout(loadTaskGroups, 500);
    })
    .catch(error => {
        console.error('Error removing task from group:', error);
        showError('移除任务失败');
    });
}

// 上移任务
function moveTaskUp(taskId) {
    fetch(`${API_BASE_URL}/task-groups/${currentTaskGroupId}`)
        .then(response => response.json())
        .then(group => {
            const taskIds = [...group.task_ids];
            const index = taskIds.indexOf(taskId);
            
            if (index <= 0) return;
            
            // 交换位置
            [taskIds[index], taskIds[index - 1]] = [taskIds[index - 1], taskIds[index]];
            
            // 更新顺序
            reorderTasksInGroup(taskIds);
        })
        .catch(error => {
            console.error('Error moving task up:', error);
            showError('移动任务失败');
        });
}

// 下移任务
function moveTaskDown(taskId) {
    fetch(`${API_BASE_URL}/task-groups/${currentTaskGroupId}`)
        .then(response => response.json())
        .then(group => {
            const taskIds = [...group.task_ids];
            const index = taskIds.indexOf(taskId);
            
            if (index === -1 || index >= taskIds.length - 1) return;
            
            // 交换位置
            [taskIds[index], taskIds[index + 1]] = [taskIds[index + 1], taskIds[index]];
            
            // 更新顺序
            reorderTasksInGroup(taskIds);
        })
        .catch(error => {
            console.error('Error moving task down:', error);
            showError('移动任务失败');
        });
}

// 重新排序任务组中的任务
function reorderTasksInGroup(taskIds) {
    fetch(`${API_BASE_URL}/task-groups/${currentTaskGroupId}/reorder`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ task_ids: taskIds })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // 刷新任务组中的任务列表
        loadTasksInGroup(data.task_ids);
    })
    .catch(error => {
        console.error('Error reordering tasks:', error);
        showError('重新排序任务失败');
    });
}

// 打开启动任务组模态框
function openStartTaskGroupModal(groupId) {
    // 重置表单
    document.getElementById('startTaskGroupForm').reset();
    document.getElementById('groupIntervalSection').style.display = 'block';
    document.getElementById('groupCronSection').style.display = 'none';
    
    // 设置任务组ID
    document.getElementById('startTaskGroupId').value = groupId;
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('startTaskGroupModal'));
    modal.show();
}

// 启动任务组
function startTaskGroup() {
    const groupId = document.getElementById('startTaskGroupId').value;
    const schedulerType = document.querySelector('input[name="groupSchedulerType"]:checked').value;
    
    // 构建配置对象
    const config = {};
    
    // 添加开始和结束时间（如果有）
    const startTime = document.getElementById('groupStartTime').value;
    if (startTime) {
        config.start_time = new Date(startTime).toISOString();
    }
    
    const endTime = document.getElementById('groupEndTime').value;
    if (endTime) {
        config.end_time = new Date(endTime).toISOString();
    }
    
    // 根据调度类型添加不同的配置
    if (schedulerType === 'interval') {
        const interval = parseInt(document.getElementById('groupInterval').value);
        if (isNaN(interval) || interval <= 0) {
            showError('请输入有效的执行间隔');
            return;
        }
        config.interval = interval;
    } else {
        const cronExpression = document.getElementById('groupCronExpression').value.trim();
        if (!cronExpression) {
            showError('请输入Cron表达式');
            return;
        }
        config.cron = cronExpression;
    }
    
    // 发送API请求
    fetch(`${API_BASE_URL}/task-groups/${groupId}/start`, {
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
        const modal = bootstrap.Modal.getInstance(document.getElementById('startTaskGroupModal'));
        modal.hide();
        
        // 提示成功
        showSuccess('任务组启动成功');
        
        // 更新UI中的任务组状态
        if (data && typeof data === 'object') {
            updateTaskGroupStatusInUI(data);
        }
        
        // 刷新任务组列表
        loadTaskGroups();
    })
    .catch(error => {
        console.error('Error starting task group:', error);
        showError('启动任务组失败');
    });
}

// 停止任务组
function stopTaskGroup(groupId) {
    if (!confirm('确定要停止此任务组吗？')) {
        return;
    }
    
    fetch(`${API_BASE_URL}/task-groups/${groupId}/stop`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        showSuccess('任务组已停止');
        
        // 更新UI中的任务组状态
        if (data && typeof data === 'object') {
            updateTaskGroupStatusInUI(data);
            
            // 找到停止按钮并替换为启动按钮
            const taskGroupRow = document.querySelector(`#taskGroupList tr[data-id="${groupId}"]`);
            if (taskGroupRow) {
                const actionsCell = taskGroupRow.querySelector('td:nth-child(7) .action-group');
                if (actionsCell) {
                    const stopButton = actionsCell.querySelector('.btn-warning');
                    if (stopButton) {
                        // 创建启动按钮
                        const startButton = document.createElement('button');
                        startButton.className = 'btn btn-sm btn-success btn-action';
                        startButton.innerHTML = '<i class="fas fa-play"></i> 启动';
                        startButton.onclick = function() { openStartTaskGroupModal(groupId); };
                        
                        // 替换按钮
                        actionsCell.replaceChild(startButton, stopButton);
                    }
                }
            }
        }
        
        // 刷新任务组列表以确保UI状态完全更新
        setTimeout(loadTaskGroups, 500);
    })
    .catch(error => {
        console.error('Error stopping task group:', error);
        showError('停止任务组失败');
    });
}

// 立即执行任务组
function executeTaskGroup(groupId) {
    fetch(`${API_BASE_URL}/task-groups/${groupId}/execute`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // 首先更新UI状态
        if (data.task_group) {
            updateTaskGroupStatusInUI(data.task_group);
        }
        
        // 检查任务组执行情况
        if (data.task_group && data.task_group.status === 'error') {
            // 如果任务组状态为错误，显示错误消息
            showError('任务组执行失败，可能原因：任务组中的任务不存在或执行出错');
            // 查看日志以获取详细信息
            setTimeout(() => {
                viewTaskLogs(groupId, data.task_group.name);
            }, 1000);
        } else {
            // 正常显示成功消息
            showSuccess(data.message || '任务组开始执行');
        }
        
        // 短暂延迟后刷新列表，以显示最新的运行状态
        setTimeout(loadTaskGroups, 1000);
    })
    .catch(error => {
        console.error('Error executing task group:', error);
        showError('执行任务组失败');
    });
}

// 更新UI中任务组的状态
function updateTaskGroupStatusInUI(taskGroup) {
    // 尝试找到列表中的任务组行
    const taskGroupRow = document.querySelector(`#taskGroupList tr[data-id="${taskGroup.id}"]`);
    if (taskGroupRow) {
        // 更新状态单元格
        const statusCell = taskGroupRow.querySelector('td:nth-child(3)');
        if (statusCell) {
            statusCell.innerHTML = `<span class="task-status status-${taskGroup.status}">${getGroupStatusText(taskGroup.status)}</span>`;
        }
        
        // 更新操作单元格，添加或移除停止按钮
        const actionsCell = taskGroupRow.querySelector('td:nth-child(7)');
        if (actionsCell) {
            const stopButtonExists = actionsCell.querySelector('.btn-warning');
            const startButtonExists = actionsCell.querySelector('.btn-success');
            
            if (taskGroup.status === 'running' && !stopButtonExists) {
                // 如果任务组正在运行但没有停止按钮，添加停止按钮
                if (startButtonExists) {
                    // 移除启动按钮
                    startButtonExists.remove();
                }
                
                // 添加停止按钮
                const stopButton = document.createElement('button');
                stopButton.className = 'btn btn-sm btn-warning btn-action';
                stopButton.innerHTML = '<i class="fas fa-stop"></i> 停止';
                stopButton.onclick = function() { stopTaskGroup(taskGroup.id); };
                
                // 找到最后一个按钮并在其前面插入停止按钮
                const lastButton = actionsCell.querySelector('.btn-danger');
                if (lastButton) {
                    actionsCell.querySelector('.action-group').insertBefore(stopButton, lastButton);
                } else {
                    actionsCell.querySelector('.action-group').appendChild(stopButton);
                }
            }
        }
    }
}

// 删除任务组
function deleteTaskGroup(groupId) {
    if (!confirm('确定要删除此任务组吗？此操作不可恢复。')) {
        return;
    }
    
    fetch(`${API_BASE_URL}/task-groups/${groupId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        showSuccess('任务组已删除');
        loadTaskGroups();
    })
    .catch(error => {
        console.error('Error deleting task group:', error);
        showError('删除任务组失败');
    });
}

// 获取任务组状态文本
function getGroupStatusText(status) {
    const statusMap = {
        'created': '已创建',
        'running': '运行中',
        'stopped': '已停止',
        'completed': '已完成',
        'error': '错误'
    };
    
    return statusMap[status] || status;
}

// 原有的任务相关功能
// ===================

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
            
            // 添加任务函数选择事件：当选择函数时，自动生成示例参数JSON或显示特定的表单
            taskFunction.addEventListener('change', function() {
                const selectedOption = this.options[this.selectedIndex];
                if (selectedOption.value) {
                    const parametersAttr = selectedOption.getAttribute('data-parameters');
                    
                    // 隐藏HTTP请求表单和普通参数输入区域
                    document.getElementById('httpRequestForm').style.display = 'none';
                    document.getElementById('normalArgsSection').style.display = 'block';
                    
                    // 特殊处理HTTP请求函数
                    if (selectedOption.value === 'http_request') {
                        document.getElementById('httpRequestForm').style.display = 'block';
                        document.getElementById('normalArgsSection').style.display = 'none';
                        
                        // 重置HTTP请求表单
                        document.getElementById('httpUrl').value = '';
                        document.getElementById('httpMethod').value = 'GET';
                        document.getElementById('httpHeaders').value = '{}';
                        document.getElementById('httpBody').value = '';
                        document.getElementById('httpTimeout').value = '30';
                        document.getElementById('httpVerify').checked = true;
                        
                        // 根据请求方法类型显示/隐藏请求体
                        updateBodyVisibility();
                        return;
                    }
                    
                    if (parametersAttr) {
                        try {
                            const parameters = JSON.parse(parametersAttr);
                            if (parameters.length > 0) {
                                const exampleArgs = {};
                                parameters.forEach(param => {
                                    if ('default' in param) {
                                        exampleArgs[param.name] = param.default;
                                    } else {
                                        // 为没有默认值的参数提供示例值
                                        exampleArgs[param.name] = null;
                                    }
                                });
                                
                                // 如果有参数，设置到文本域
                                if (Object.keys(exampleArgs).length > 0) {
                                    document.getElementById('taskArgs').value = JSON.stringify(exampleArgs, null, 2);
                                } else {
                                    document.getElementById('taskArgs').value = '{}';
                                }
                            } else {
                                document.getElementById('taskArgs').value = '{}';
                            }
                        } catch (e) {
                            console.error('解析函数参数失败', e);
                            document.getElementById('taskArgs').value = '{}';
                        }
                    } else {
                        document.getElementById('taskArgs').value = '{}';
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading functions:', error);
            showError('加载任务函数列表失败');
        });
}

// 根据HTTP请求方法类型更新请求体输入框的可见性
function updateBodyVisibility() {
    const method = document.getElementById('httpMethod').value;
    const bodyContainer = document.getElementById('httpBodyContainer');
    
    // 对于GET、HEAD、OPTIONS方法，通常不需要请求体
    if (method === 'GET' || method === 'HEAD' || method === 'OPTIONS') {
        bodyContainer.style.display = 'none';
    } else {
        bodyContainer.style.display = 'block';
    }
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
                    <td>${escapeHtml(task.name)}<br><small class="text-muted">ID: ${task.id}</small></td>
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
            
            // 保存当前任务ID，用于编辑功能
            currentTaskId = task.id;
            
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
                <tr>
                    <th>函数参数</th>
                    <td><pre class="bg-light p-2 rounded">${escapeHtml(JSON.stringify(task.args, null, 2))}</pre></td>
                </tr>
            </table>
            `;
            
            document.getElementById('taskDetailContent').innerHTML = html;
            
            // 添加任务操作按钮
            let actionsHtml = `
                <button class="btn btn-info" onclick="editTask()">
                    <i class="fas fa-edit"></i> 编辑任务
                </button>
                <button class="btn btn-secondary" onclick="viewTaskLogs('${task.id}', '${escapeHtml(task.name)}')">
                    <i class="fas fa-list-alt"></i> 查看日志
                </button>
                ${task.status !== 'running' ? 
                `<button class="btn btn-success" onclick="openStartTaskModal('${task.id}')">
                    <i class="fas fa-play"></i> 启动任务
                </button>
                <button class="btn btn-primary" onclick="executeTask('${task.id}')">
                    <i class="fas fa-bolt"></i> 立即执行
                </button>` : ''}
                
                ${task.status === 'running' ? 
                `<button class="btn btn-warning" onclick="stopTask('${task.id}')">
                    <i class="fas fa-stop"></i> 停止任务
                </button>` : ''}
            `;
            
            document.getElementById('taskDetailActions').innerHTML = actionsHtml;
            
            // 隐藏编辑表单
            document.getElementById('taskEditForm').style.display = 'none';
            document.getElementById('taskDetailContent').style.display = 'block';
            document.getElementById('taskDetailActions').style.display = 'flex';
            
            // 显示详情模态框
            const modal = new bootstrap.Modal(document.getElementById('taskDetailModal'));
            modal.show();

            // 监听模态框关闭事件
            document.getElementById('taskDetailModal').addEventListener('hidden.bs.modal', function () {
                // 重置状态
                currentTaskId = null;
                document.getElementById('taskDetailContent').innerHTML = '';
                document.getElementById('taskDetailActions').innerHTML = '';
            });
        })
        .catch(error => {
            console.error('Error viewing task details:', error);
            showError('加载任务详情失败');
        });
}

// 编辑任务
function editTask() {
    const taskId = currentTaskId;
    
    fetch(`${API_BASE_URL}/tasks/${taskId}`)
        .then(response => response.json())
        .then(task => {
            // 检查是否有错误
            if (task.error) {
                showError(task.error);
                return;
            }
            
            // 隐藏详情区域，显示编辑表单
            document.getElementById('taskDetailContent').style.display = 'none';
            document.getElementById('taskDetailActions').style.display = 'none';
            document.getElementById('taskEditForm').style.display = 'block';
            
            // 填充表单
            document.getElementById('editTaskId').value = task.id;
            document.getElementById('editTaskName').value = task.name;
            
            // 加载函数列表并设置选择
            loadFunctionsForEdit();
            
            // 在函数列表加载完成后处理
            const functionSelect = document.getElementById('editTaskFunction');
            functionSelect.addEventListener('load', function() {
                // 选择对应的函数
                for (let i = 0; i < functionSelect.options.length; i++) {
                    if (functionSelect.options[i].value === task.function) {
                        functionSelect.selectedIndex = i;
                        break;
                    }
                }
                
                // 根据任务类型显示对应表单并填充数据
                if (task.function === 'http_request') {
                    // 显示HTTP请求表单
                    document.getElementById('editNormalArgsSection').style.display = 'none';
                    document.getElementById('editHttpRequestForm').style.display = 'block';
                    
                    // 填充HTTP请求表单数据
                    if (task.args) {
                        document.getElementById('editHttpUrl').value = task.args.url || '';
                        document.getElementById('editHttpMethod').value = task.args.method || 'GET';
                        document.getElementById('editHttpHeaders').value = JSON.stringify(task.args.headers || {}, null, 2);
                        
                        if (task.args.body) {
                            document.getElementById('editHttpBody').value = typeof task.args.body === 'object' 
                                ? JSON.stringify(task.args.body, null, 2) 
                                : task.args.body;
                        } else {
                            document.getElementById('editHttpBody').value = '';
                        }
                        
                        document.getElementById('editHttpTimeout').value = task.args.timeout || 30;
                        document.getElementById('editHttpVerify').checked = task.args.verify !== false;
                    }
                    
                    // 更新请求体显示
                    updateEditBodyVisibility();
                } else {
                    // 显示普通参数表单
                    document.getElementById('editNormalArgsSection').style.display = 'block';
                    document.getElementById('editHttpRequestForm').style.display = 'none';
                    
                    // 填充任务参数
                    if (task.args) {
                        document.getElementById('editTaskArgs').value = JSON.stringify(task.args, null, 2);
                    } else {
                        document.getElementById('editTaskArgs').value = '{}';
                    }
                }
            }, { once: true });
            
            // 设置取消按钮点击事件
            document.getElementById('cancelEditBtn').onclick = function() {
                document.getElementById('taskEditForm').style.display = 'none';
                document.getElementById('taskDetailContent').style.display = 'block';
                document.getElementById('taskDetailActions').style.display = 'flex';
            };
            
            // 设置保存按钮点击事件
            document.getElementById('saveTaskBtn').onclick = function() {
                saveTaskChanges();
            };
        })
        .catch(error => {
            console.error('Error loading task for edit:', error);
            showError('加载任务信息失败');
        });
}

// 加载函数列表到编辑表单
function loadFunctionsForEdit() {
    fetch(`${API_BASE_URL}/functions`)
        .then(response => response.json())
        .then(data => {
            const functionSelect = document.getElementById('editTaskFunction');
            
            // 清空现有选项
            while (functionSelect.options.length > 0) {
                functionSelect.remove(0);
            }
            
            // 添加默认选项
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = '请选择函数';
            functionSelect.appendChild(defaultOption);
            
            // 添加函数选项
            data.functions.forEach(func => {
                const option = document.createElement('option');
                option.value = func.name;
                
                // 提取简短描述（第一行）
                const shortDesc = func.description.split('\n')[0];
                option.textContent = `${func.name} - ${shortDesc}`;
                
                // 添加函数参数信息作为自定义属性
                option.setAttribute('data-description', func.description);
                option.setAttribute('data-parameters', JSON.stringify(func.parameters));
                
                functionSelect.appendChild(option);
            });
            
            // 设置函数选择事件监听
            functionSelect.addEventListener('change', function() {
                const selectedOption = this.options[this.selectedIndex];
                if (selectedOption.value) {
                    const parametersAttr = selectedOption.getAttribute('data-parameters');
                    
                    // 隐藏HTTP请求表单和普通参数输入区域
                    document.getElementById('editHttpRequestForm').style.display = 'none';
                    document.getElementById('editNormalArgsSection').style.display = 'block';
                    
                    // 特殊处理HTTP请求函数
                    if (selectedOption.value === 'http_request') {
                        document.getElementById('editHttpRequestForm').style.display = 'block';
                        document.getElementById('editNormalArgsSection').style.display = 'none';
                        
                        // 设置默认值
                        document.getElementById('editHttpUrl').value = '';
                        document.getElementById('editHttpMethod').value = 'GET';
                        document.getElementById('editHttpHeaders').value = '{}';
                        document.getElementById('editHttpBody').value = '';
                        document.getElementById('editHttpTimeout').value = '30';
                        document.getElementById('editHttpVerify').checked = true;
                        
                        // 根据请求方法更新表单显示
                        updateEditBodyVisibility();
                        return;
                    }
                    
                    // 为普通函数生成参数示例
                    if (parametersAttr) {
                        try {
                            const parameters = JSON.parse(parametersAttr);
                            if (parameters.length > 0) {
                                const exampleArgs = {};
                                parameters.forEach(param => {
                                    if ('default' in param) {
                                        exampleArgs[param.name] = param.default;
                                    } else {
                                        // 为没有默认值的参数提供示例值
                                        exampleArgs[param.name] = null;
                                    }
                                });
                                
                                // 如果有参数，设置到文本域
                                if (Object.keys(exampleArgs).length > 0) {
                                    document.getElementById('editTaskArgs').value = JSON.stringify(exampleArgs, null, 2);
                                } else {
                                    document.getElementById('editTaskArgs').value = '{}';
                                }
                            } else {
                                document.getElementById('editTaskArgs').value = '{}';
                            }
                        } catch (e) {
                            console.error('解析函数参数失败', e);
                            document.getElementById('editTaskArgs').value = '{}';
                        }
                    } else {
                        document.getElementById('editTaskArgs').value = '{}';
                    }
                }
            });
            
            // 触发加载完成事件
            functionSelect.dispatchEvent(new Event('load'));
        })
        .catch(error => {
            console.error('Error loading functions for edit:', error);
            showError('加载任务函数列表失败');
        });
}

// 处理函数变更，显示对应的表单
function handleEditFunctionChange(task = null) {
    const functionName = document.getElementById('editTaskFunction').value;
    const normalArgsSection = document.getElementById('editNormalArgsSection');
    const httpRequestForm = document.getElementById('editHttpRequestForm');
    
    // 根据选择的函数显示不同的表单
    if (functionName === 'http_request') {
        normalArgsSection.style.display = 'none';
        httpRequestForm.style.display = 'block';
        
        // 如果有任务数据，填充HTTP请求表单
        if (task && task.args) {
            document.getElementById('editHttpUrl').value = task.args.url || '';
            document.getElementById('editHttpMethod').value = task.args.method || 'GET';
            document.getElementById('editHttpHeaders').value = JSON.stringify(task.args.headers || {}, null, 2);
            
            if (task.args.body) {
                document.getElementById('editHttpBody').value = typeof task.args.body === 'object' 
                    ? JSON.stringify(task.args.body, null, 2) 
                    : task.args.body;
            } else {
                document.getElementById('editHttpBody').value = '';
            }
            
            document.getElementById('editHttpTimeout').value = task.args.timeout || 30;
            document.getElementById('editHttpVerify').checked = task.args.verify !== false;
        } else {
            // 如果没有任务数据，设置默认值
            document.getElementById('editHttpUrl').value = '';
            document.getElementById('editHttpMethod').value = 'GET';
            document.getElementById('editHttpHeaders').value = '{}';
            document.getElementById('editHttpBody').value = '';
            document.getElementById('editHttpTimeout').value = '30';
            document.getElementById('editHttpVerify').checked = true;
            updateEditBodyVisibility();
        }
    } else {
        normalArgsSection.style.display = 'block';
        httpRequestForm.style.display = 'none';
        
        // 如果有任务数据，填充普通参数
        if (task && task.args) {
            document.getElementById('editTaskArgs').value = JSON.stringify(task.args, null, 2);
        } else {
            // 生成示例参数
            generateExampleParams(functionName);
        }
    }
}

// 生成并显示函数的示例参数
function generateExampleParams(functionName) {
    // 如果没有选择函数，使用空对象
    if (!functionName) {
        document.getElementById('editTaskArgs').value = '{}';
        return;
    }
    
    // 查找选中的函数选项
    const functionSelect = document.getElementById('editTaskFunction');
    const selectedOption = Array.from(functionSelect.options).find(option => option.value === functionName);
    
    if (selectedOption) {
        const parametersAttr = selectedOption.getAttribute('data-parameters');
        
        if (parametersAttr) {
            try {
                const parameters = JSON.parse(parametersAttr);
                if (parameters.length > 0) {
                    const exampleArgs = {};
                    parameters.forEach(param => {
                        if ('default' in param) {
                            exampleArgs[param.name] = param.default;
                        } else {
                            // 为没有默认值的参数提供示例值
                            exampleArgs[param.name] = null;
                        }
                    });
                    
                    // 设置示例参数到文本域
                    document.getElementById('editTaskArgs').value = JSON.stringify(exampleArgs, null, 2);
                    return;
                }
            } catch (e) {
                console.error('解析函数参数失败', e);
            }
        }
    }
    
    // 如果没有找到参数或发生错误，使用空对象
    document.getElementById('editTaskArgs').value = '{}';
}

// 更新编辑表单中HTTP请求体的显示状态
function updateEditBodyVisibility() {
    const method = document.getElementById('editHttpMethod').value;
    const bodyContainer = document.getElementById('editHttpBodyContainer');
    
    if (method === 'GET' || method === 'HEAD' || method === 'OPTIONS') {
        bodyContainer.style.display = 'none';
    } else {
        bodyContainer.style.display = 'block';
    }
}

// 保存任务修改
function saveTaskChanges() {
    const taskId = document.getElementById('editTaskId').value;
    const name = document.getElementById('editTaskName').value.trim();
    const functionName = document.getElementById('editTaskFunction').value;
    let args = {};
    
    // 验证输入
    if (!name) {
        showError('请输入任务名称');
        return;
    }
    
    if (!functionName) {
        showError('请选择任务函数');
        return;
    }
    
    // 根据选择的函数获取不同的参数
    if (functionName === 'http_request') {
        const url = document.getElementById('editHttpUrl').value.trim();
        const method = document.getElementById('editHttpMethod').value;
        let headers = document.getElementById('editHttpHeaders').value.trim();
        let body = document.getElementById('editHttpBody').value.trim();
        const timeout = parseInt(document.getElementById('editHttpTimeout').value) || 30;
        const verify = document.getElementById('editHttpVerify').checked;
        
        // 验证URL
        if (!url) {
            showError('请输入请求URL');
            return;
        }
        
        // 解析headers
        try {
            headers = headers ? JSON.parse(headers) : {};
        } catch (e) {
            showError('请求头格式不正确，请使用有效的JSON格式');
            return;
        }
        
        // 解析body（仅对POST、PUT等方法）
        if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS' && body) {
            try {
                // 尝试解析为JSON，失败则保留为字符串
                if (body.trim().startsWith('{') || body.trim().startsWith('[')) {
                    body = JSON.parse(body);
                }
            } catch (e) {
                // 如果解析失败，保留为字符串
                console.log('Body is not a valid JSON, keeping as string');
            }
        }
        
        // 构建HTTP请求参数
        args = {
            url: url,
            method: method,
            headers: headers,
            timeout: timeout,
            verify: verify
        };
        
        // 仅当有请求体且不是GET/HEAD/OPTIONS方法时添加body
        if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS' && body) {
            args.body = body;
        }
    } else {
        // 普通参数
        try {
            args = JSON.parse(document.getElementById('editTaskArgs').value);
        } catch (e) {
            showError('函数参数格式不正确，请使用有效的JSON格式');
            return;
        }
    }
    
    // 构建请求数据
    const taskData = {
        name: name,
        function: functionName,
        args: args
    };
    
    // 发送API请求
    fetch(`${API_BASE_URL}/tasks/${taskId}`, {
        method: 'PUT',
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
        
        // 显示成功消息
        showSuccess('任务更新成功');
        
        // 刷新任务详情
        viewTaskDetail(taskId);
        
        // 刷新任务列表
        loadTasks();
    })
    .catch(error => {
        console.error('Error updating task:', error);
        showError('更新任务失败');
    });
}

// 查看任务日志
function viewTaskLogs(id, name) {
    // 保存当前任务/任务组信息
    currentTaskId = id;
    currentTaskName = name;
    
    // 设置模态框标题
    document.getElementById('taskLogsModalLabel').textContent = `日志: ${name}`;
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('taskLogsModal'));
    modal.show();
    
    // 加载日志
    loadTaskLogs();
}

// 查看全局日志
function viewAllLogs() {
    // 清除当前任务/任务组信息，表示查看全局日志
    currentTaskId = null;
    currentTaskName = null;
    
    // 显示日志模态框
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
    
    // 设置模态框标题
    const titleText = currentTaskId ? `${currentTaskName} 日志` : '全局日志';
    document.getElementById('taskLogsModalLabel').textContent = titleText;
    
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
                throw new Error(`HTTP错误 ${response.status}: ${response.statusText || ''}`);
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
                logsList.innerHTML = `<tr><td colspan="3" class="text-center">暂无日志数据${currentTaskName ? ` (${currentTaskName})` : ''}</td></tr>`;
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
            const diagnosticMessage = getLogDiagnosticMessage(errorMessage, currentTaskId);
            
            document.getElementById('logsList').innerHTML = `
                <tr><td colspan="3" class="text-center text-danger">加载日志失败: ${escapeHtml(errorMessage)}</td></tr>
                <tr><td colspan="3" class="text-center">${diagnosticMessage}</td></tr>
            `;
        });
}

// 获取日志错误的诊断信息
function getLogDiagnosticMessage(errorMessage, taskId) {
    if (errorMessage.includes('HTTP错误 404')) {
        return `
            <div class="alert alert-info mt-2">
                <h5>找不到日志</h5>
                <p>可能的原因：</p>
                <ul>
                    <li>指定的任务或任务组不存在</li>
                    <li>任务或任务组尚未生成任何日志</li>
                    <li>日志文件已被清理或移动</li>
                </ul>
                <p>建议尝试查看全局日志，或确认任务/任务组ID是否正确。</p>
            </div>
        `;
    } else if (errorMessage.includes('UnicodeDecodeError') || errorMessage.includes('invalid')) {
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
    
    // 验证输入
    if (!name) {
        showError('请输入任务名称');
        return;
    }
    
    if (!functionName) {
        showError('请选择任务函数');
        return;
    }
    
    // 特殊处理HTTP请求
    if (functionName === 'http_request') {
        const url = document.getElementById('httpUrl').value.trim();
        if (!url) {
            showError('请输入请求URL');
            return;
        }
        
        args.url = url;
        args.method = document.getElementById('httpMethod').value;
        
        // 解析请求头JSON
        const headersText = document.getElementById('httpHeaders').value.trim();
        if (headersText) {
            try {
                args.headers = JSON.parse(headersText);
            } catch (e) {
                showError('请求头格式不正确，请输入有效的JSON格式');
                return;
            }
        } else {
            args.headers = {};
        }
        
        // 解析请求体（仅对非GET请求）
        if (args.method !== 'GET' && args.method !== 'HEAD' && args.method !== 'OPTIONS') {
            const bodyText = document.getElementById('httpBody').value.trim();
            if (bodyText) {
                // 尝试解析为JSON对象
                try {
                    args.body = JSON.parse(bodyText);
                } catch (e) {
                    // 如果不是有效的JSON，则作为字符串处理
                    args.body = bodyText;
                }
            }
        }
        
        // 添加超时和SSL验证参数
        args.timeout = parseInt(document.getElementById('httpTimeout').value) || 30;
        args.verify = document.getElementById('httpVerify').checked;
    } else {
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
        document.getElementById('httpRequestForm').style.display = 'none';
        document.getElementById('normalArgsSection').style.display = 'block';
        
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
    if (!confirm('确定要删除此任务吗？此操作不可恢复。如果该任务已被添加到任务组中，相关任务组也会同步更新。')) {
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
        
        // 检查是否有受影响的任务组
        if (data.affected_groups && data.affected_groups.length > 0) {
            const groupNames = data.affected_groups.map(g => g.name).join(', ');
            showSuccess(`任务已删除，并从以下任务组中移除: ${groupNames}`);
            
            // 刷新任务组列表
            setTimeout(loadTaskGroups, 500);
        } else {
            showSuccess('任务已删除');
        }
        
        // 刷新任务列表
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

// 清除日志
function clearLogs() {
    const days = document.getElementById('logDays').value;
    const daysText = days > 0 ? `最近${days}天的` : '所有';
    const targetText = currentTaskId ? `当前${currentTaskName}的${daysText}` : daysText;
    
    // 确认是否要清除日志
    Swal.fire({
        title: '确认清除日志',
        text: `您确定要清除${targetText}日志吗？此操作不可撤销，但会自动创建备份。`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: '确认清除',
        cancelButtonText: '取消'
    }).then((result) => {
        if (result.isConfirmed) {
            // 构建API URL
            let url = `${API_BASE_URL}/logs`;
            if (currentTaskId) {
                url += `/${currentTaskId}`;
            }
            url += `?days=${days}`;
            
            // 调用API删除日志
            fetch(url, {
                method: 'DELETE'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP错误 ${response.status}: ${response.statusText || ''}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    Swal.fire({
                        title: '日志已清除',
                        text: data.message,
                        icon: 'success',
                        confirmButtonColor: '#28a745'
                    });
                    
                    // 刷新日志显示
                    loadTaskLogs();
                } else {
                    throw new Error(data.message || '清除日志失败');
                }
            })
            .catch(error => {
                console.error('Error clearing logs:', error);
                Swal.fire({
                    title: '操作失败',
                    text: `清除日志时出错: ${error.message}`,
                    icon: 'error',
                    confirmButtonColor: '#dc3545'
                });
            });
        }
    });
} 