document.addEventListener('DOMContentLoaded', function() {
    // DOM 元素
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');
    const roomsContainer = document.getElementById('rooms-container');
    const serviceQueueContainer = document.getElementById('service-queue-container');
    const waitingQueueContainer = document.getElementById('waiting-queue-container');
    const roomSearchInput = document.getElementById('room-search');
    const searchBtn = document.getElementById('search-btn');
    const systemOnBtn = document.getElementById('system-on-btn');
    const systemOffBtn = document.getElementById('system-off-btn');
    const roomControlModal = document.getElementById('room-control-modal');
    const alertModal = document.getElementById('alert-modal');
    const modalRoomTitle = document.getElementById('modal-room-title');
    const roomStateSelect = document.getElementById('room-state');
    const roomModeSelect = document.getElementById('room-mode');
    const roomTempInput = document.getElementById('room-temp');
    const roomSpeedSelect = document.getElementById('room-speed');
    const currentTempSpan = document.getElementById('current-temp');
    const currentBillSpan = document.getElementById('current-bill');
    const applySettingsBtn = document.getElementById('apply-settings-btn');
    const closeModalBtns = document.querySelectorAll('.close-modal');
    const cancelBtns = document.querySelectorAll('.cancel-btn');
    const connectionStatus = document.getElementById('connection-status');
    const connectionText = document.getElementById('connection-text');
    const alertTitle = document.getElementById('alert-title');
    const alertMessage = document.getElementById('alert-message');

    // WebSocket 连接
    let roomInfoSocket = null;
    let scheduleSocket = null;
    let roomDetailSocket = null; // 新增：用于查询房间详情的单一WebSocket连接
    let currentRoomId = null;
    let roomsData = {};
    let servingQueue = [];
    let waitingQueue = [];

    // 初始化
    initWebSockets();
    initEventListeners();

    // 初始化 WebSocket 连接
    function initWebSockets() {
        updateConnectionStatus('正在连接...', 'connecting');

        // 连接房间信息 WebSocket
        roomInfoSocket = new WebSocket('ws://127.0.0.1:10043/ws/roominfo');
        
        roomInfoSocket.onopen = function() {
            console.log('房间信息 WebSocket 已连接');
            updateConnectionStatus('已连接', 'connected');
            requestRoomInfo();
        };
        
        roomInfoSocket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.rooms) {
                handleRoomsData(data.rooms);
            }
        };
        
        roomInfoSocket.onerror = function(error) {
            console.error('房间信息 WebSocket 错误:', error);
            updateConnectionStatus('连接错误', 'disconnected');
            showAlert('连接错误', '无法连接到房间信息服务，请检查网络或服务器状态。');
        };
        
        roomInfoSocket.onclose = function() {
            console.log('房间信息 WebSocket 已关闭');
            updateConnectionStatus('未连接', 'disconnected');
            
            // 尝试重新连接
            setTimeout(function() {
                if (roomInfoSocket.readyState === WebSocket.CLOSED) {
                    initWebSockets();
                }
            }, 5000);
        };

        // 连接调度信息 WebSocket
        scheduleSocket = new WebSocket('ws://127.0.0.1:10043/ws/query_schedule');
        
        scheduleSocket.onopen = function() {
            console.log('调度信息 WebSocket 已连接');
            requestScheduleInfo();
        };
        
        scheduleSocket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.serving_queue && data.waiting_queue) {
                servingQueue = data.serving_queue;
                waitingQueue = data.waiting_queue;
                renderQueues();
            }
        };
        
        scheduleSocket.onerror = function(error) {
            console.error('调度信息 WebSocket 错误:', error);
            showAlert('连接错误', '无法连接到调度信息服务，请检查网络或服务器状态。');
        };
        
        scheduleSocket.onclose = function() {
            console.log('调度信息 WebSocket 已关闭');
            
            // 尝试重新连接
            setTimeout(function() {
                if (scheduleSocket.readyState === WebSocket.CLOSED) {
                    scheduleSocket = new WebSocket('ws://127.0.0.1:10043/ws/query_schedule');
                }
            }, 5000);
        };

        // 新增：连接房间详情查询 WebSocket
        roomDetailSocket = new WebSocket('ws://127.0.0.1:10043/ws/query_room_info');
        
        roomDetailSocket.onopen = function() {
            console.log('房间详情 WebSocket 已连接');
        };
        
        roomDetailSocket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.roomId) {
                // 根据返回的roomId更新对应房间信息
                updateRoomData(data.roomId, data);
            } else {
                console.warn('收到的房间详情数据没有roomId:', data);
            }
        };
        
        roomDetailSocket.onerror = function(error) {
            console.error('房间详情 WebSocket 错误:', error);
            showAlert('连接错误', '无法连接到房间详情服务，请检查网络或服务器状态。');
        };
        
        roomDetailSocket.onclose = function() {
            console.log('房间详情 WebSocket 已关闭');
            
            // 尝试重新连接
            setTimeout(function() {
                if (roomDetailSocket.readyState === WebSocket.CLOSED) {
                    roomDetailSocket = new WebSocket('ws://127.0.0.1:10043/ws/query_room_info');
                }
            }, 5000);
        };
    }

    // 初始化事件监听器
    function initEventListeners() {
        // 导航标签切换
        navItems.forEach(item => {
            item.addEventListener('click', function() {
                navItems.forEach(nav => nav.classList.remove('active'));
                this.classList.add('active');
                
                const tabId = this.getAttribute('data-tab');
                tabContents.forEach(tab => tab.classList.remove('active'));
                document.getElementById(tabId).classList.add('active');
            });
        });

        // 搜索房间
        searchBtn.addEventListener('click', searchRoom);
        roomSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchRoom();
            }
        });

        // 系统控制按钮
        systemOnBtn.addEventListener('click', function() {
            showAlert('系统操作', '确定要开启所有房间的空调吗？', function() {
                setAllRoomsState('on');
            });
        });

        systemOffBtn.addEventListener('click', function() {
            showAlert('系统操作', '确定要关闭所有房间的空调吗？', function() {
                setAllRoomsState('off');
            });
        });

        // 应用房间设置按钮
        applySettingsBtn.addEventListener('click', applyRoomSettings);

        // 关闭模态框按钮
        closeModalBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                roomControlModal.style.display = 'none';
                alertModal.style.display = 'none';
            });
        });

        // 取消按钮
        cancelBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                roomControlModal.style.display = 'none';
                alertModal.style.display = 'none';
            });
        });

        // 点击模态框外部关闭
        window.addEventListener('click', function(event) {
            if (event.target === roomControlModal) {
                roomControlModal.style.display = 'none';
            }
            if (event.target === alertModal) {
                alertModal.style.display = 'none';
            }
        });

        // 退出系统按钮
        document.getElementById('logout-btn').addEventListener('click', function(e) {
            e.preventDefault();
            showAlert('退出系统', '确定要退出系统吗？', function() {
                // 关闭所有WebSocket连接
                if (roomInfoSocket) roomInfoSocket.close();
                if (scheduleSocket) scheduleSocket.close();
                
                // 重定向到登录页面
                window.location.href = '../index.html';
            });
        });
    }

    // 更新连接状态指示器
    function updateConnectionStatus(text, status) {
        connectionText.textContent = text;
        connectionStatus.className = status;
    }

    // 请求房间信息
    function requestRoomInfo() {
        if (roomInfoSocket.readyState === WebSocket.OPEN) {
            roomInfoSocket.send(JSON.stringify({ request: 1 }));
        } else {
            console.error('房间信息WebSocket未连接');
        }
    }

    // 请求调度信息
    function requestScheduleInfo() {
        if (scheduleSocket.readyState === WebSocket.OPEN) {
            scheduleSocket.send(JSON.stringify({ request: 1 }));
        } else {
            console.error('调度信息WebSocket未连接');
        }
    }

    // 处理房间数据
    function handleRoomsData(rooms) {
        roomsContainer.innerHTML = '';
        
        if (rooms.length === 0) {
            roomsContainer.innerHTML = '<div class="queue-empty">暂无房间信息</div>';
            return;
        }
        
        rooms.forEach(room => {
            const roomId = room.roomId;
            
            // 存储房间基本信息
            if (!roomsData[roomId]) {
                roomsData[roomId] = {
                    id: roomId,
                    status: room.status || 'unknown',
                    currentTemp: '--',
                    targetTemp: '--',
                    mode: '--',
                    speed: '--',
                    bill: 0
                };
            } else {
                roomsData[roomId].status = room.status || roomsData[roomId].status;
            }
            
            // 创建房间卡片
            createRoomCard(roomId);
            
            // 请求房间详细信息
            requestRoomDetailInfo(roomId);
        });
    }

    // 请求房间详细信息 - 修改后的函数
    function requestRoomDetailInfo(roomId) {
        if (roomDetailSocket && roomDetailSocket.readyState === WebSocket.OPEN) {
            roomDetailSocket.send(JSON.stringify({ roomId: roomId }));
        } else {
            console.error(`房间详情WebSocket未连接，无法请求房间 ${roomId} 的详细信息`);
            // 如果连接未就绪，5秒后重试
            setTimeout(function() {
                if (roomDetailSocket && roomDetailSocket.readyState === WebSocket.OPEN) {
                    roomDetailSocket.send(JSON.stringify({ roomId: roomId }));
                }
            }, 5000);
        }
    }

    // 更新房间数据
    function updateRoomData(roomId, data) {
        if (!roomsData[roomId]) return;
        
        roomsData[roomId].status = data.status !== undefined ? data.status : roomsData[roomId].status;
        roomsData[roomId].currentTemp = data.now_temp !== undefined ? data.now_temp : roomsData[roomId].currentTemp;
        roomsData[roomId].targetTemp = data.set_temp !== undefined ? data.set_temp : roomsData[roomId].targetTemp;
        roomsData[roomId].mode = data.mode !== undefined ? data.mode : roomsData[roomId].mode;
        roomsData[roomId].speed = data.speed !== undefined ? data.speed : roomsData[roomId].speed;
        roomsData[roomId].bill = data.bill !== undefined ? data.bill : roomsData[roomId].bill;
        
        // 更新房间卡片
        updateRoomCard(roomId);
        
        // 如果当前有房间设置模态框打开，更新其中的信息
        if (currentRoomId === roomId && roomControlModal.style.display === 'flex') {
            currentTempSpan.textContent = roomsData[roomId].currentTemp;
            currentBillSpan.textContent = parseFloat(roomsData[roomId].bill).toFixed(2);
        }
    }

    // 创建房间卡片
    function createRoomCard(roomId) {
        const card = document.createElement('div');
        card.className = 'room-card';
        card.dataset.roomId = roomId;
        
        card.innerHTML = `
            <div class="room-header">
                <h3 class="room-title">
                    <img src="./icons/空调.svg" alt="Room" class="room-icon">
                    房间 ${roomId}
                </h3>
                <span class="room-status">加载中...</span>
            </div>
            <div class="room-info">
                <div class="info-item">
                    <span class="info-label">当前温度:</span>
                    <span class="current-temp">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">目标温度:</span>
                    <span class="target-temp">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">工作模式:</span>
                    <span class="mode">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">风速:</span>
                    <span class="speed">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">当前账单:</span>
                    <span class="bill">0.00 元</span>
                </div>
            </div>
            <div class="room-actions">
                <button class="control-btn" data-room-id="${roomId}">
                    <img src="./icons/configure.svg" alt="Control" class="action-icon">
                    控制
                </button>
            </div>
        `;
        
        roomsContainer.appendChild(card);
        
        // 添加控制按钮事件
        const controlBtn = card.querySelector('.control-btn');
        controlBtn.addEventListener('click', function() {
            openRoomControlModal(roomId);
        });
    }

    // 更新房间卡片
    function updateRoomCard(roomId) {
        const card = document.querySelector(`.room-card[data-room-id="${roomId}"]`);
        if (!card) {
            console.error(`未找到房间卡片元素: ${roomId}`);
            return;
        }
        
        const room = roomsData[roomId];
        const statusElement = card.querySelector('.room-status');
        const currentTempElement = card.querySelector('.current-temp');
        const targetTempElement = card.querySelector('.target-temp');
        const modeElement = card.querySelector('.mode');
        const speedElement = card.querySelector('.speed');
        const billElement = card.querySelector('.bill');
        
        // 更新状态
        let statusText = '未知';
        let statusClass = '';
        
        switch (room.status) {
            case 'running':
                statusText = '服务中';
                statusClass = 'status-running';
                break;
            case 'waiting':
                statusText = '等待中';
                statusClass = 'status-waiting';
                break;
            case 'off':
                statusText = '已关闭';
                statusClass = 'status-off';
                break;
            case 'free':
                statusText = '空闲';
                statusClass = 'status-free';
                break;
            case 'busy':
                statusText = '占用';
                statusClass = 'status-busy';
                break;
        }
        
        statusElement.textContent = statusText;
        statusElement.className = 'room-status ' + statusClass;
        
        // 更新温度
        currentTempElement.textContent = `${room.currentTemp}°C`;
        targetTempElement.textContent = `${room.targetTemp}°C`;
        
        // 更新模式
        let modeText = room.mode;
        if (room.mode === 'cool') modeText = '制冷';
        if (room.mode === 'heat') modeText = '制热';
        modeElement.textContent = modeText;
        
        // 更新风速
        let speedText = room.speed;
        if (room.speed === 0 || room.speed === '0') speedText = '低风速';
        if (room.speed === 1 || room.speed === '1') speedText = '中风速';
        if (room.speed === 2 || room.speed === '2') speedText = '高风速';
        speedElement.textContent = speedText;
        
        // 更新账单
        billElement.textContent = `${parseFloat(room.bill).toFixed(2)} 元`;
    }

    // 渲染队列
    function renderQueues() {
        // 渲染服务队列
        serviceQueueContainer.innerHTML = '';
        
        if (servingQueue.length === 0) {
            serviceQueueContainer.innerHTML = '<div class="queue-empty">当前服务队列为空</div>';
        } else {
            servingQueue.forEach(roomId => {
                const queueItem = document.createElement('div');
                queueItem.className = 'queue-item';
                
                queueItem.innerHTML = `
                    <div class="room-id">房间 ${roomId}</div>
                    <button class="control-btn" data-room-id="${roomId}">
                        <img src="./icons/configure.svg" alt="Control" class="action-icon">
                        控制
                    </button>
                `;
                
                serviceQueueContainer.appendChild(queueItem);
                
                // 添加控制按钮事件
                const controlBtn = queueItem.querySelector('.control-btn');
                controlBtn.addEventListener('click', function() {
                    openRoomControlModal(roomId);
                });
            });
        }
        
        // 渲染等待队列
        waitingQueueContainer.innerHTML = '';
        
        if (waitingQueue.length === 0) {
            waitingQueueContainer.innerHTML = '<div class="queue-empty">当前等待队列为空</div>';
        } else {
            waitingQueue.forEach(roomId => {
                const queueItem = document.createElement('div');
                queueItem.className = 'queue-item';
                
                queueItem.innerHTML = `
                    <div class="room-id">房间 ${roomId}</div>
                    <button class="control-btn" data-room-id="${roomId}">
                        <img src="./icons/configure.svg" alt="Control" class="action-icon">
                        控制
                    </button>
                `;
                
                waitingQueueContainer.appendChild(queueItem);
                
                // 添加控制按钮事件
                const controlBtn = queueItem.querySelector('.control-btn');
                controlBtn.addEventListener('click', function() {
                    openRoomControlModal(roomId);
                });
            });
        }
    }

    // 打开房间控制模态框
    function openRoomControlModal(roomId) {
        if (!roomsData[roomId]) {
            showAlert('错误', `无法获取房间 ${roomId} 的信息`);
            return;
        }
        
        currentRoomId = roomId;
        const room = roomsData[roomId];
        
        modalRoomTitle.textContent = `房间 ${roomId} 控制`;
        
        // 设置当前值
        roomStateSelect.value = room.status === 'off' ? 'off' : 'on';
        roomModeSelect.value = room.mode === 'heat' ? 'heat' : 'cool';
        roomTempInput.value = room.targetTemp !== '--' ? room.targetTemp : 25;
        roomSpeedSelect.value = room.speed !== '--' ? room.speed : 0;
        currentTempSpan.textContent = room.currentTemp !== '--' ? room.currentTemp : '--';
        currentBillSpan.textContent = parseFloat(room.bill).toFixed(2);
        
        // 显示模态框
        roomControlModal.style.display = 'flex';
    }

    // 应用房间设置
    function applyRoomSettings() {
        if (!currentRoomId || !roomsData[currentRoomId]) {
            showAlert('错误', '无法应用设置，房间信息不可用');
            return;
        }
        
        const room = roomsData[currentRoomId];
        const newState = roomStateSelect.value;
        const newMode = roomModeSelect.value;
        const newTemp = parseFloat(roomTempInput.value);
        const newSpeed = parseInt(roomSpeedSelect.value);
        
        // 验证温度值
        if (isNaN(newTemp) || newTemp < 16 || newTemp > 30) {
            showAlert('错误', '目标温度必须在16°C到30°C之间');
            return;
        }
        
        // 创建WebSocket连接发送控制命令
        const controlSocket = new WebSocket(`ws://127.0.0.1:10043/ws/room?roomId=000`);
        
        controlSocket.onopen = function() {
            const controlData = {
                roomId: currentRoomId,
                state: newState,
                speed: newSpeed,
                now_temp: room.currentTemp !== '--' ? room.currentTemp : 25,
                set_temp: newTemp,
                mode: newMode,
                new_request: 1
            };
            
            controlSocket.send(JSON.stringify(controlData));
        };
        
        controlSocket.onmessage = function(event) {
            const response = JSON.parse(event.data);
            
            if (response.state === 'off' && newState === 'on') {
                showAlert('操作结果', `房间 ${currentRoomId} 无法开启，可能已被系统关闭。`);
            } else {
                showAlert('操作结果', `房间 ${currentRoomId} 设置已应用成功！`);
                
                // 更新房间数据
                roomsData[currentRoomId].status = newState === 'on' ? 'running' : 'off';
                roomsData[currentRoomId].mode = newMode;
                roomsData[currentRoomId].targetTemp = newTemp;
                roomsData[currentRoomId].speed = newSpeed;
                if (response.bill !== undefined) {
                    roomsData[currentRoomId].bill = response.bill;
                }
                
                // 更新UI
                updateRoomCard(currentRoomId);
                
                // 刷新调度信息
                requestScheduleInfo();
            }
            
            controlSocket.close();
        };
        
        controlSocket.onerror = function(error) {
            console.error('控制WebSocket错误:', error);
            showAlert('错误', `无法发送控制命令到房间 ${currentRoomId}，请检查网络连接。`);
            controlSocket.close();
        };
        
        // 关闭模态框
        roomControlModal.style.display = 'none';
    }

    // 设置所有房间状态
    function setAllRoomsState(state) {
        const roomIds = Object.keys(roomsData);
        
        if (roomIds.length === 0) {
            showAlert('提示', '没有可用的房间');
            return;
        }
        
        let successCount = 0;
        let totalCount = roomIds.length;
        let completedCount = 0;
        
        roomIds.forEach(roomId => {
            const room = roomsData[roomId];
            
            // 如果房间已经是目标状态，跳过
            if ((state === 'on' && room.status === 'running') || 
                (state === 'off' && room.status === 'off')) {
                completedCount++;
                if (completedCount === totalCount) {
                    showAlert('操作完成', `已${state === 'on' ? '开启' : '关闭'}所有房间，成功: ${successCount}，跳过: ${totalCount - successCount}`);
                }
                return;
            }
            
            const controlSocket = new WebSocket(`ws://127.0.0.1:10043/ws/room?roomId=${roomId}`);
            
            controlSocket.onopen = function() {
                const controlData = {
                    roomId: roomId,
                    state: state,
                    speed: room.speed !== '--' ? room.speed : 0,
                    now_temp: room.currentTemp !== '--' ? room.currentTemp : 25,
                    set_temp: room.targetTemp !== '--' ? room.targetTemp : 25,
                    mode: room.mode !== '--' ? room.mode : 'cool',
                    new_request: 1
                };
                
                controlSocket.send(JSON.stringify(controlData));
            };
            
            controlSocket.onmessage = function(event) {
                completedCount++;
                
                const response = JSON.parse(event.data);
                if ((state === 'on' && response.state === 'on') || 
                    (state === 'off' && response.state === 'off')) {
                    successCount++;
                    
                    // 更新房间数据
                    roomsData[roomId].status = state === 'on' ? 'running' : 'off';
                    if (response.bill !== undefined) {
                        roomsData[roomId].bill = response.bill;
                    }
                    
                    // 更新UI
                    updateRoomCard(roomId);
                }
                
                if (completedCount === totalCount) {
                    showAlert('操作完成', `已${state === 'on' ? '开启' : '关闭'}所有房间，成功: ${successCount}，失败: ${totalCount - successCount}`);
                    
                    // 刷新调度信息
                    requestScheduleInfo();
                    
                    // 刷新房间状态
                    requestRoomInfo();
                }
                
                controlSocket.close();
            };
            
            controlSocket.onerror = function() {
                completedCount++;
                controlSocket.close();
                
                if (completedCount === totalCount) {
                    showAlert('操作完成', `已${state === 'on' ? '开启' : '关闭'}所有房间，成功: ${successCount}，失败: ${totalCount - successCount}`);
                    
                    // 刷新调度信息
                    requestScheduleInfo();
                    
                    // 刷新房间状态
                    requestRoomInfo();
                }
            };
        });
    }

    // 搜索房间
    function searchRoom() {
        const searchText = roomSearchInput.value.trim().toLowerCase();
        const roomCards = document.querySelectorAll('.room-card');
        
        roomCards.forEach(card => {
            const roomId = card.dataset.roomId;
            if (roomId.toLowerCase().includes(searchText)) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    }

    // 显示提示模态框
    function showAlert(title, message, callback) {
        alertTitle.textContent = title;
        alertMessage.textContent = message;
        
        // 如果提供了回调函数，则为确定按钮添加事件
        const confirmBtn = alertModal.querySelector('.primary-btn');
        
        if (callback) {
            confirmBtn.onclick = function() {
                callback();
                alertModal.style.display = 'none';
                confirmBtn.onclick = function() {
                    alertModal.style.display = 'none';
                };
            };
        } else {
            confirmBtn.onclick = function() {
                alertModal.style.display = 'none';
            };
        }
        
        alertModal.style.display = 'flex';
    }

    // 定期刷新数据
    setInterval(function() {
        if (roomInfoSocket.readyState === WebSocket.OPEN) {
            requestRoomInfo();
        }
        
        if (scheduleSocket.readyState === WebSocket.OPEN) {
            requestScheduleInfo();
        }
        
        // 定期刷新每个房间的详细信息
        if (roomDetailSocket.readyState === WebSocket.OPEN) {
            Object.keys(roomsData).forEach(roomId => {
                requestRoomDetailInfo(roomId);
            });
        }
    }, 10000); // 每10秒刷新一次
});