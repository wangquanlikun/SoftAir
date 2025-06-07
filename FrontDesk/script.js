// 全局变量
const BASE_WS_URL = 'ws://127.0.0.1:10043/ws';
let roomInfoSocket = null;
let checkinSocket = null;
let checkoutSocket = null;
let billSocket = null;
let useListSocket = null;
let allRooms = [];
let currentView = 'all';

// DOM 元素
const navAllRooms = document.getElementById('nav-all-rooms');
const navOccupiedRooms = document.getElementById('nav-occupied-rooms');
const navVacantRooms = document.getElementById('nav-vacant-rooms');

const allRoomsView = document.getElementById('all-rooms-view');
const occupiedRoomsView = document.getElementById('occupied-rooms-view');
const vacantRoomsView = document.getElementById('vacant-rooms-view');

const allRoomsContainer = document.getElementById('all-rooms-container');
const occupiedRoomsContainer = document.getElementById('occupied-rooms-container');
const vacantRoomsContainer = document.getElementById('vacant-rooms-container');

const searchInput = document.getElementById('room-search-input');
const searchButton = document.getElementById('search-room-button');
const refreshButton = document.getElementById('refresh-button');
const checkInButton = document.getElementById('check-in-button');
const checkOutButton = document.getElementById('check-out-button');

// 弹窗相关元素
const modalCheckIn = document.getElementById('modal-check-in');
const modalCheckOut = document.getElementById('modal-check-out');
const modalBillDetail = document.getElementById('modal-bill-detail');
const modalMessage = document.getElementById('modal-message');

const checkinGuestName = document.getElementById('checkin-guest-name');
const checkinGuestId = document.getElementById('checkin-guest-id');
const checkinRoomSelect = document.getElementById('checkin-room-select');
const confirmCheckInButton = document.getElementById('confirm-check-in-button');
const cancelCheckInButton = document.getElementById('cancel-check-in-button');
const closeCheckIn = document.getElementById('close-check-in');

const checkoutRoomSelect = document.getElementById('checkout-room-select');
const checkoutInfo = document.getElementById('checkout-info');
const checkoutRoomId = document.getElementById('checkout-room-id');
const checkoutTotalCost = document.getElementById('checkout-total-cost');
const viewBillButton = document.getElementById('view-bill-button');
const viewDetailButton = document.getElementById('view-detail-button');
const confirmCheckOutButton = document.getElementById('confirm-check-out-button');
const cancelCheckOutButton = document.getElementById('cancel-check-out-button');
const closeCheckOut = document.getElementById('close-check-out');

const billDetailTitle = document.getElementById('bill-detail-title');
const billDetailContent = document.getElementById('bill-detail-content');
const printBillDetailButton = document.getElementById('print-bill-detail-button');
const closeBillDetailButton = document.getElementById('close-bill-detail-button');
const closeBillDetail = document.getElementById('close-bill-detail');

const messageTitle = document.getElementById('message-title');
const messageContent = document.getElementById('message-content');
const messageConfirmButton = document.getElementById('message-confirm-button');

// 全局变量和DOM元素引用部分，添加新元素引用
const detailQueryOptions = document.getElementById('detail-query-options');
const userQueryOptions = document.getElementById('user-query-options');
const timeQueryOptions = document.getElementById('time-query-options');
const detailUserIdInput = document.getElementById('detail-user-id');
const detailStartTimeInput = document.getElementById('detail-start-time');
const detailEndTimeInput = document.getElementById('detail-end-time');
const submitDetailQueryButton = document.getElementById('submit-detail-query');
const queryTypeRadios = document.getElementsByName('query-type');

// 初始化函数
function init() {
    // 初始化WebSocket连接
    connectToRoomInfoSocket();
    connectToCheckinSocket();
    connectToCheckoutSocket();
    connectToBillSocket();
    connectToUselistSocket();
    
    // 绑定事件处理
    bindEventListeners();
}

// 建立WebSocket连接
function connectToRoomInfoSocket() {
    roomInfoSocket = new WebSocket(`${BASE_WS_URL}/roominfo`);
    
    roomInfoSocket.onopen = () => {
        console.log('房间信息WebSocket连接已建立');
        fetchRoomInfo(); // 加载房间数据
    };
    
    roomInfoSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        processRoomInfo(data);
    };
    
    roomInfoSocket.onclose = () => {
        console.log('房间信息WebSocket连接已关闭');
        setTimeout(connectToRoomInfoSocket, 3000); // 尝试重新连接
    };
    
    roomInfoSocket.onerror = (error) => {
        console.error('房间信息WebSocket错误:', error);
    };
}

function connectToCheckinSocket() {
    checkinSocket = new WebSocket(`${BASE_WS_URL}/checkin`);
    
    checkinSocket.onopen = () => {
        console.log('入住WebSocket连接已建立');
    };
    
    checkinSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        processCheckinResponse(data);
    };
    
    checkinSocket.onclose = () => {
        console.log('入住WebSocket连接已关闭');
        setTimeout(connectToCheckinSocket, 3000);
    };
    
    checkinSocket.onerror = (error) => {
        console.error('入住WebSocket错误:', error);
    };
}

function connectToCheckoutSocket() {
    checkoutSocket = new WebSocket(`${BASE_WS_URL}/checkout`);
    
    checkoutSocket.onopen = () => {
        console.log('退房WebSocket连接已建立');
    };
    
    checkoutSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        processCheckoutResponse(data);
    };
    
    checkoutSocket.onclose = () => {
        console.log('退房WebSocket连接已关闭');
        setTimeout(connectToCheckoutSocket, 3000);
    };
    
    checkoutSocket.onerror = (error) => {
        console.error('退房WebSocket错误:', error);
    };
}

function connectToBillSocket() {
    billSocket = new WebSocket(`${BASE_WS_URL}/bill`);
    
    billSocket.onopen = () => {
        console.log('账单WebSocket连接已建立');
    };
    
    billSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        processBillResponse(data);
    };
    
    billSocket.onclose = () => {
        console.log('账单WebSocket连接已关闭');
        setTimeout(connectToBillSocket, 3000);
    };
    
    billSocket.onerror = (error) => {
        console.error('账单WebSocket错误:', error);
    };
}

function connectToUselistSocket() {
    useListSocket = new WebSocket(`${BASE_WS_URL}/uselist`);
    
    useListSocket.onopen = () => {
        console.log('详单WebSocket连接已建立');
    };
    
    useListSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        processUselistResponse(data);
    };
    
    useListSocket.onclose = () => {
        console.log('详单WebSocket连接已关闭');
        setTimeout(connectToUselistSocket, 3000);
    };
    
    useListSocket.onerror = (error) => {
        console.error('详单WebSocket错误:', error);
    };
}

// 绑定事件监听
function bindEventListeners() {
    // 导航切换
    navAllRooms.addEventListener('click', () => switchView('all'));
    navOccupiedRooms.addEventListener('click', () => switchView('occupied'));
    navVacantRooms.addEventListener('click', () => switchView('vacant'));
    
    // 搜索功能
    searchButton.addEventListener('click', searchRooms);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchRooms();
    });
    
    // 刷新按钮
    refreshButton.addEventListener('click', fetchRoomInfo);
    
    // 开房和退房按钮
    checkInButton.addEventListener('click', openCheckInModal);
    checkOutButton.addEventListener('click', openCheckOutModal);
    
    // 开房弹窗相关
    confirmCheckInButton.addEventListener('click', handleCheckin);
    cancelCheckInButton.addEventListener('click', () => closeModal(modalCheckIn));
    closeCheckIn.addEventListener('click', () => closeModal(modalCheckIn));
    
    // 退房弹窗相关
    checkoutRoomSelect.addEventListener('change', handleCheckoutRoomSelect);
    viewBillButton.addEventListener('click', requestBill);
    viewDetailButton.addEventListener('click', requestUselist);
    confirmCheckOutButton.addEventListener('click', handleCheckout);
    cancelCheckOutButton.addEventListener('click', () => closeModal(modalCheckOut));
    closeCheckOut.addEventListener('click', () => closeModal(modalCheckOut));
    
    // 账单/详单弹窗相关
    printBillDetailButton.addEventListener('click', printBillDetail);
    closeBillDetailButton.addEventListener('click', () => closeModal(modalBillDetail));
    closeBillDetail.addEventListener('click', () => closeModal(modalBillDetail));
    
    // 消息弹窗
    messageConfirmButton.addEventListener('click', () => closeModal(modalMessage));
    
    // 查询方式单选按钮切换事件
    queryTypeRadios.forEach(radio => {
        radio.addEventListener('change', toggleQueryOptions);
    });
    
    // 提交详单查询按钮
    submitDetailQueryButton.addEventListener('click', submitDetailQuery);
}

// 切换视图
function switchView(view) {
    currentView = view;
    
    // 更新导航项状态
    navAllRooms.classList.remove('active');
    navOccupiedRooms.classList.remove('active');
    navVacantRooms.classList.remove('active');
    
    // 隐藏所有视图
    allRoomsView.style.display = 'none';
    occupiedRoomsView.style.display = 'none';
    vacantRoomsView.style.display = 'none';
    
    // 显示选中的视图
    switch (view) {
        case 'all':
            navAllRooms.classList.add('active');
            allRoomsView.style.display = 'block';
            break;
        case 'occupied':
            navOccupiedRooms.classList.add('active');
            occupiedRoomsView.style.display = 'block';
            break;
        case 'vacant':
            navVacantRooms.classList.add('active');
            vacantRoomsView.style.display = 'block';
            break;
    }
    
    // 更新房间显示
    renderRooms();
}

// 请求房间信息
function fetchRoomInfo() {
    if (roomInfoSocket && roomInfoSocket.readyState === WebSocket.OPEN) {
        roomInfoSocket.send(JSON.stringify({ request: 1 }));
    } else {
        showMessage('连接错误', '无法连接到服务器，请检查网络连接后重试。');
    }
}

// 处理房间信息响应
function processRoomInfo(data) {
    if (data && data.rooms) {
        allRooms = data.rooms;
        renderRooms();
        updateRoomSelects();
    }
}

// 渲染房间列表
function renderRooms() {
    const searchTerm = searchInput.value.toLowerCase();
    const filteredRooms = searchTerm 
        ? allRooms.filter(room => room.roomId.toLowerCase().includes(searchTerm))
        : allRooms;
    
    // 清空容器
    allRoomsContainer.innerHTML = '';
    occupiedRoomsContainer.innerHTML = '';
    vacantRoomsContainer.innerHTML = '';
    
    if (filteredRooms.length === 0) {
        const placeholderAll = document.createElement('p');
        placeholderAll.className = 'placeholder-text';
        placeholderAll.textContent = searchTerm ? '没有找到匹配的房间' : '暂无房间信息';
        allRoomsContainer.appendChild(placeholderAll);
        
        const placeholderOccupied = placeholderAll.cloneNode(true);
        occupiedRoomsContainer.appendChild(placeholderOccupied);
        
        const placeholderVacant = placeholderAll.cloneNode(true);
        vacantRoomsContainer.appendChild(placeholderVacant);
        return;
    }
    
    // 渲染房间卡片
    filteredRooms.forEach(room => {
        const isFree = room.status === 'free';
        const card = createRoomCard(room);
        
        // 添加到所有房间视图
        allRoomsContainer.appendChild(card.cloneNode(true));
        
        // 添加到对应状态的视图
        if (isFree) {
            vacantRoomsContainer.appendChild(card.cloneNode(true));
        } else {
            occupiedRoomsContainer.appendChild(card.cloneNode(true));
        }
    });
    
    // 如果筛选后没有房间，显示提示
    if (occupiedRoomsContainer.children.length === 0) {
        const placeholderOccupied = document.createElement('p');
        placeholderOccupied.className = 'placeholder-text';
        placeholderOccupied.textContent = '暂无已入住房间';
        occupiedRoomsContainer.appendChild(placeholderOccupied);
    }
    
    if (vacantRoomsContainer.children.length === 0) {
        const placeholderVacant = document.createElement('p');
        placeholderVacant.className = 'placeholder-text';
        placeholderVacant.textContent = '暂无空闲房间';
        vacantRoomsContainer.appendChild(placeholderVacant);
    }
}

// 创建房间卡片
function createRoomCard(room) {
    const isFree = room.status === 'free';
    
    const card = document.createElement('div');
    card.className = `room-card ${isFree ? 'room-free' : 'room-busy'}`;
    card.dataset.roomId = room.roomId;
    
    const statusBadge = document.createElement('div');
    statusBadge.className = `status-badge ${isFree ? 'status-free' : 'status-busy'}`;
    statusBadge.textContent = isFree ? '空闲' : '已入住';
    card.appendChild(statusBadge);
    
    const header = document.createElement('div');
    header.className = 'room-card-header';
    
    const title = document.createElement('h4');
    title.textContent = `房间 ${room.roomId}`;
    header.appendChild(title);
    
    card.appendChild(header);
    
    const statusText = document.createElement('p');
    statusText.innerHTML = `<strong>状态:</strong> ${isFree ? '空闲' : '已入住'}`;
    card.appendChild(statusText);
    
    const actions = document.createElement('div');
    actions.className = 'room-card-actions';
    
    if (isFree) {
        const checkInBtn = document.createElement('button');
        checkInBtn.className = 'card-action-button';
        checkInBtn.textContent = '入住';
        checkInBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            openCheckInModal(room.roomId);
        });
        actions.appendChild(checkInBtn);
    } else {
        const checkOutBtn = document.createElement('button');
        checkOutBtn.className = 'card-action-button';
        checkOutBtn.textContent = '退房';
        checkOutBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            openCheckOutModal(room.roomId);
        });
        actions.appendChild(checkOutBtn);
    }
    
    card.appendChild(actions);
    
    return card;
}

// 更新房间选择下拉框
function updateRoomSelects() {
    // 更新开房房间选择
    checkinRoomSelect.innerHTML = '<option value="000">自动分配房间</option>';
    
    const freeRooms = allRooms.filter(room => room.status === 'free');
    freeRooms.forEach(room => {
        const option = document.createElement('option');
        option.value = room.roomId;
        option.textContent = `房间 ${room.roomId}`;
        checkinRoomSelect.appendChild(option);
    });
    
    // 更新退房房间选择
    checkoutRoomSelect.innerHTML = '<option value="">请选择房间</option>';
    
    const busyRooms = allRooms.filter(room => room.status === 'busy');
    busyRooms.forEach(room => {
        const option = document.createElement('option');
        option.value = room.roomId;
        option.textContent = `房间 ${room.roomId}`;
        checkoutRoomSelect.appendChild(option);
    });
}

// 搜索房间
function searchRooms() {
    renderRooms();
}

// 打开入住弹窗
function openCheckInModal(roomId = '') {
    checkinGuestName.value = '';
    checkinGuestId.value = '';
    
    if (roomId) {
        // 如果指定了房间号，选择对应选项
        Array.from(checkinRoomSelect.options).forEach(option => {
            if (option.value === roomId) {
                option.selected = true;
            }
        });
    } else {
        // 否则默认为自动分配
        checkinRoomSelect.value = '000';
    }
    
    openModal(modalCheckIn);
}

// 打开退房弹窗
function openCheckOutModal(roomId = '') {
    checkoutInfo.style.display = 'none';
    
    if (roomId) {
        // 如果指定了房间号，选择对应选项
        Array.from(checkoutRoomSelect.options).forEach(option => {
            if (option.value === roomId) {
                option.selected = true;
                handleCheckoutRoomSelect();
            }
        });
    } else {
        // 否则清空选择
        checkoutRoomSelect.value = '';
    }
    
    openModal(modalCheckOut);
}

// 处理退房房间选择
function handleCheckoutRoomSelect() {
    const roomId = checkoutRoomSelect.value;
    
    if (roomId) {
        // 显示房间信息
        checkoutRoomId.textContent = roomId;
        
        // 请求账单信息
        if (billSocket && billSocket.readyState === WebSocket.OPEN) {
            billSocket.send(JSON.stringify({ roomId }));
        } else {
            showMessage('连接错误', '无法连接到账单服务，请稍后再试。');
        }
        
        checkoutInfo.style.display = 'block';
    } else {
        checkoutInfo.style.display = 'none';
    }
}

// 处理开房请求
function handleCheckin() {
    const name = checkinGuestName.value.trim();
    const id = checkinGuestId.value.trim();
    const roomId = checkinRoomSelect.value;
    
    if (!name) {
        showMessage('信息不完整', '请输入顾客姓名。');
        return;
    }
    
    if (!id) {
        showMessage('信息不完整', '请输入顾客身份证号。');
        return;
    }
    
    // 验证身份证号格式（简单验证）
    if (!/^\d{17}[\dXx]$/.test(id)) {
        showMessage('格式错误', '请输入有效的18位身份证号码。');
        return;
    }
    
    const data = {
        roomId,
        client_name: name,
        client_id: id
    };
    
    if (checkinSocket && checkinSocket.readyState === WebSocket.OPEN) {
        checkinSocket.send(JSON.stringify(data));
    } else {
        showMessage('连接错误', '无法连接到服务器，请稍后再试。');
    }
}

// 处理退房请求
function handleCheckout() {
    const roomId = checkoutRoomSelect.value;
    
    if (!roomId) {
        showMessage('信息不完整', '请选择要退房的房间。');
        return;
    }
    
    if (checkoutSocket && checkoutSocket.readyState === WebSocket.OPEN) {
        checkoutSocket.send(JSON.stringify({ roomId }));
    } else {
        showMessage('连接错误', '无法连接到服务器，请稍后再试。');
    }
}

// 请求账单
function requestBill() {
    const roomId = checkoutRoomSelect.value;
    
    if (!roomId) {
        showMessage('信息不完整', '请先选择房间。');
        return;
    }
    
    if (billSocket && billSocket.readyState === WebSocket.OPEN) {
        billSocket.send(JSON.stringify({ roomId }));
        billDetailTitle.textContent = `房间 ${roomId} 账单信息`;
        openModal(modalBillDetail);
    } else {
        showMessage('连接错误', '无法连接到账单服务，请稍后再试。');
    }
}

// 请求详单
function requestUselist() {
    const roomId = checkoutRoomSelect.value;
    
    if (!roomId) {
        showMessage('信息不完整', '请先选择房间。');
        return;
    }
    
    // 设置默认时间（过去30天）
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    detailStartTimeInput.value = formatDatetimeLocal(startDate);
    detailEndTimeInput.value = formatDatetimeLocal(endDate);
    
    // 清空用户ID输入
    detailUserIdInput.value = '';
    
    // 显示查询选项
    detailQueryOptions.style.display = 'block';
    billDetailContent.innerHTML = '<p class="placeholder-text">请选择查询方式并提交查询</p>';
    billDetailTitle.textContent = `房间 ${roomId} 详单查询`;
    
    // 重置为默认查询方式
    document.querySelector('input[name="query-type"][value="user"]').checked = true;
    toggleQueryOptions();
    
    openModal(modalBillDetail);
}

// 格式化日期为datetime-local输入框格式
function formatDatetimeLocal(date) {
    return date.toISOString().slice(0, 16); // 格式: YYYY-MM-DDTHH:MM
}

// 切换查询选项显示
function toggleQueryOptions() {
    const queryType = document.querySelector('input[name="query-type"]:checked').value;
    
    if (queryType === 'user') {
        userQueryOptions.style.display = 'block';
        timeQueryOptions.style.display = 'none';
    } else if (queryType === 'time') {
        userQueryOptions.style.display = 'none';
        timeQueryOptions.style.display = 'block';
    }
}

// 提交详单查询
function submitDetailQuery() {
    const roomId = checkoutRoomSelect.value;
    const queryType = document.querySelector('input[name="query-type"]:checked').value;
    let data = {};
    
    if (queryType === 'user') {
        // 按用户ID查询
        const userId = detailUserIdInput.value.trim();
        if (!userId) {
            showMessage('信息不完整', '请输入用户身份证号。');
            return;
        }
        
        data = {
            roomId,
            type: 'usr',
            usrId: userId,
            start_time: 'NULL',
            end_time: 'NULL'
        };
        
    } else if (queryType === 'time') {
        // 按时间范围查询
        const startTime = detailStartTimeInput.value;
        const endTime = detailEndTimeInput.value;
        
        if (!startTime || !endTime) {
            showMessage('信息不完整', '请选择开始和结束时间。');
            return;
        }
        
        data = {
            roomId,
            type: 'room',
            usrId: 'NULL',
            start_time: formatDateForServer(new Date(startTime)),
            end_time: formatDateForServer(new Date(endTime))
        };
    }
    
    // 隐藏查询选项，显示加载提示
    detailQueryOptions.style.display = 'none';
    billDetailContent.innerHTML = '<p class="placeholder-text">正在加载详单数据...</p>';
    
    // 发送详单查询请求
    if (useListSocket && useListSocket.readyState === WebSocket.OPEN) {
        useListSocket.send(JSON.stringify(data));
    } else {
        showMessage('连接错误', '无法连接到详单服务，请稍后再试。');
    }
}

// 格式化日期为服务器请求格式
function formatDateForServer(date) {
    return date.toISOString().replace('T', ' ').substring(0, 19);
}

// 处理开房响应
function processCheckinResponse(data) {
    if (data.status === 'OK') {
        closeModal(modalCheckIn);
        showMessage('开房成功', `房间号: ${data.allocate_room} 已成功办理入住。`);
        fetchRoomInfo(); // 刷新房间状态
    } else {
        showMessage('开房失败', '无空闲房间可分配或服务器错误，请稍后再试。');
    }
}

// 处理退房响应
function processCheckoutResponse(data) {
    if (data.status === 'OK') {
        closeModal(modalCheckOut);
        showMessage('退房成功', `退房已完成，消费总额: ${data.bill.toFixed(2)} 元。`);
        fetchRoomInfo(); // 刷新房间状态
    } else {
        showMessage('退房失败', '服务器处理退房请求时出错，请稍后再试。');
    }
}

// 处理账单响应
function processBillResponse(data) {
    // 更新退房弹窗中的金额
    checkoutTotalCost.textContent = data.bill.toFixed(2);
    
    // 如果账单弹窗打开，更新其内容
    if (modalBillDetail.style.display === 'flex') {
        const billContent = `
            <div class="bill-summary">
                <p><strong>房间号:</strong> ${checkoutRoomSelect.value}</p>
                <p><strong>总消费金额:</strong> ${data.bill.toFixed(2)} 元</p>
                <p><strong>生成时间:</strong> ${new Date().toLocaleString()}</p>
            </div>
        `;
        billDetailContent.innerHTML = billContent;
    }
}

// 处理详单响应
function processUselistResponse(data) {
    if (modalBillDetail.style.display === 'flex') {
        billDetailContent.innerHTML = `
            <div class="uselist-content">
                <h4>使用记录:</h4>
                <pre>${data.uselist || '暂无详细使用记录'}</pre>
            </div>
        `;
    }
}

// 打印账单/详单
function printBillDetail() {
    const printContent = billDetailContent.innerHTML;
    const printWindow = window.open('', '_blank');
    
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>打印账单</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h1 { text-align: center; color: #07B2D9; }
                .bill-summary p { margin: 10px 0; }
                pre { white-space: pre-wrap; }
            </style>
        </head>
        <body>
            <h1>${billDetailTitle.textContent}</h1>
            ${printContent}
        </body>
        </html>
    `);
    
    printWindow.document.close();
    printWindow.focus();
    
    // 稍微延迟以确保内容加载完成
    setTimeout(() => {
        printWindow.print();
        printWindow.close();
    }, 250);
}

// 显示消息弹窗
function showMessage(title, message) {
    messageTitle.textContent = title;
    messageContent.textContent = message;
    openModal(modalMessage);
}

// 打开弹窗
function openModal(modal) {
    modal.style.display = 'flex';
}

// 关闭弹窗
function closeModal(modal) {
    modal.style.display = 'none';
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);