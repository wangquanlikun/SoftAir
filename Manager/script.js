document.addEventListener('DOMContentLoaded', () => {
    // DOM元素
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const viewReportButton = document.getElementById('view-report-button');
    const exportReportButton = document.getElementById('export-report-button');
    const printReportButton = document.getElementById('print-report-button');
    const reportContentEl = document.getElementById('report-content');
    const modalError = document.getElementById('modal-error');
    const modalText = document.getElementById('modal-text');
    const closeModalButton = document.getElementById('close-modal-button');
    const modalConfirmButton = document.getElementById('modal-confirm-button');
    const connectionIndicator = document.getElementById('connection-indicator');
    const connectionText = document.getElementById('connection-text');
    const loadingIndicator = document.getElementById('loading-indicator');
    const logoutButton = document.getElementById('logout-button');

    // WebSocket连接
    let socket = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    let currentReportData = null;

    // 设置默认日期和时间 (当前日期的00:00到23:59)
    const setDefaultDates = () => {
        const today = new Date();
        const startDay = new Date(today);
        startDay.setDate(startDay.getDate() - 7); // 一周前
        startDay.setHours(0, 0, 0, 0);
        
        const endDay = new Date(today);
        endDay.setHours(23, 59, 0, 0);
        
        startDateInput.value = formatDateTimeForInput(startDay);
        endDateInput.value = formatDateTimeForInput(endDay);
    };

    // 格式化日期时间为input[type="datetime-local"]格式
    function formatDateTimeForInput(date) {
        return date.toISOString().slice(0, 16);
    }

    // 格式化日期时间为WebSocket请求格式
    function formatDateTimeForWS(dateString) {
        const date = new Date(dateString);
        return date.toISOString().replace('T', ' ').slice(0, 19);
    }

    // 显示模态框
    function showModal(message) {
        modalText.textContent = message;
        modalError.style.display = 'flex';
    }

    // 关闭模态框
    function closeModal() {
        modalError.style.display = 'none';
    }

    // 连接WebSocket
    function connectWebSocket() {
        try {
            if (socket && socket.readyState !== WebSocket.CLOSED) {
                return; // 已经连接
            }
            
            socket = new WebSocket('ws://127.0.0.1:10043/ws/manager');
            
            socket.onopen = () => {
                console.log('WebSocket连接已建立');
                updateConnectionStatus(true);
                reconnectAttempts = 0;
            };
            
            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleReportData(data);
            };
            
            socket.onclose = (event) => {
                console.log('WebSocket连接已关闭', event.code, event.reason);
                updateConnectionStatus(false);
                
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    console.log(`尝试重新连接 (${reconnectAttempts}/${maxReconnectAttempts})...`);
                    setTimeout(connectWebSocket, 3000);
                } else {
                    showModal('无法连接到服务器，请检查网络连接后刷新页面。');
                }
            };
            
            socket.onerror = (error) => {
                console.error('WebSocket错误:', error);
                updateConnectionStatus(false);
            };
        } catch (error) {
            console.error('建立WebSocket连接时发生错误:', error);
            updateConnectionStatus(false);
            showModal('连接服务器失败，请稍后再试。');
        }
    }

    // 更新连接状态指示器
    function updateConnectionStatus(isConnected) {
        if (isConnected) {
            connectionIndicator.className = 'indicator connected';
            connectionText.textContent = '已连接';
        } else {
            connectionIndicator.className = 'indicator disconnected';
            connectionText.textContent = '未连接';
        }
    }

    // 发送报表请求
    function requestReport(startDate, endDate) {
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            showModal('未连接到服务器，请稍后再试。');
            return;
        }
        
        setLoading(true);
        
        const requestData = {
            start_time: formatDateTimeForWS(startDate),
            end_time: formatDateTimeForWS(endDate)
        };
        
        console.log('发送报表请求:', requestData);
        socket.send(JSON.stringify(requestData));
    }

    // 处理接收到的报表数据
    function handleReportData(data) {
        setLoading(false);
        
        if (!data || !data.content) {
            showModal('接收到的报表数据无效或为空。');
            return;
        }
        
        currentReportData = data;
        displayReport(data.content);
        
        // 启用导出和打印按钮
        exportReportButton.disabled = false;
        printReportButton.disabled = false;
    }

    // 显示报表数据
    function displayReport(content) {
        // 清空之前的内容
        reportContentEl.innerHTML = '';
        reportContentEl.className = 'report-content';
        
        try {
            // 尝试解析数据为JSON，如果是JSON字符串
            let reportData;
            try {
                reportData = typeof content === 'string' ? JSON.parse(content) : content;
            } catch (e) {
                // 如果不是JSON，直接使用内容
                reportData = content;
            }
            
            // 如果是简单字符串，直接显示
            if (typeof reportData === 'string') {
                const contentP = document.createElement('p');
                contentP.textContent = reportData;
                reportContentEl.appendChild(contentP);
                return;
            }
            
            // 根据数据创建表格
            const table = document.createElement('table');
            table.id = 'report-table';
            
            // 如果是数组类型的数据，创建表格
            if (Array.isArray(reportData)) {
                if (reportData.length === 0) {
                    const noDataP = document.createElement('p');
                    noDataP.textContent = '所选日期范围内没有数据。';
                    reportContentEl.appendChild(noDataP);
                    return;
                }
                
                // 创建表头
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                
                // 使用第一个对象的键作为表头
                const headers = Object.keys(reportData[0]);
                headers.forEach(headerText => {
                    const th = document.createElement('th');
                    th.textContent = headerText;
                    headerRow.appendChild(th);
                });
                
                thead.appendChild(headerRow);
                table.appendChild(thead);
                
                // 创建表体
                const tbody = document.createElement('tbody');
                reportData.forEach(item => {
                    const row = document.createElement('tr');
                    Object.values(item).forEach(value => {
                        const td = document.createElement('td');
                        td.textContent = value;
                        row.appendChild(td);
                    });
                    tbody.appendChild(row);
                });
                
                table.appendChild(tbody);
                reportContentEl.appendChild(table);
            } else {
                // 对象类型数据，创建键值对列表
                for (const [key, value] of Object.entries(reportData)) {
                    const item = document.createElement('div');
                    item.className = 'report-item';
                    
                    const itemKey = document.createElement('span');
                    itemKey.className = 'report-key';
                    itemKey.textContent = key + ': ';
                    
                    const itemValue = document.createElement('span');
                    itemValue.className = 'report-value';
                    itemValue.textContent = value;
                    
                    item.appendChild(itemKey);
                    item.appendChild(itemValue);
                    reportContentEl.appendChild(item);
                }
            }
        } catch (error) {
            console.error('显示报表数据时出错:', error);
            const errorP = document.createElement('p');
            errorP.textContent = '无法显示报表数据，格式不正确。原始数据: ' + content;
            reportContentEl.appendChild(errorP);
        }
    }

    // 设置加载状态
    function setLoading(isLoading) {
        if (isLoading) {
            loadingIndicator.style.display = 'flex';
            reportContentEl.style.display = 'none';
        } else {
            loadingIndicator.style.display = 'none';
            reportContentEl.style.display = 'block';
        }
    }

    // 导出报表为CSV
    function exportReportAsCSV() {
        if (!currentReportData) {
            showModal('没有可导出的数据。');
            return;
        }
        
        try {
            let csvContent = '';
            let reportData;
            
            try {
                reportData = typeof currentReportData.content === 'string' 
                    ? JSON.parse(currentReportData.content) 
                    : currentReportData.content;
            } catch (e) {
                reportData = currentReportData.content;
                if (typeof reportData === 'string') {
                    showModal('当前数据格式不适合导出为CSV。');
                    return;
                }
            }
            
            if (Array.isArray(reportData)) {
                // 创建表头
                const headers = Object.keys(reportData[0]);
                csvContent += headers.join(',') + '\n';
                
                // 添加数据行
                reportData.forEach(item => {
                    const row = Object.values(item).join(',');
                    csvContent += row + '\n';
                });
                
                // 创建下载链接
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.setAttribute('download', `报表_${new Date().toISOString().slice(0, 10)}.csv`);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } else {
                showModal('当前数据格式不适合导出为CSV。');
            }
        } catch (error) {
            console.error('导出CSV时出错:', error);
            showModal('导出报表失败。');
        }
    }

    // 打印报表
    function printReport() {
        window.print();
    }

    // 事件监听器
    viewReportButton.addEventListener('click', () => {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        
        if (!startDate || !endDate) {
            showModal('请选择起始和结束日期。');
            return;
        }
        
        if (new Date(startDate) > new Date(endDate)) {
            showModal('起始日期不能晚于结束日期。');
            return;
        }
        
        requestReport(startDate, endDate);
    });
    
    exportReportButton.addEventListener('click', exportReportAsCSV);
    printReportButton.addEventListener('click', printReport);
    
    closeModalButton.addEventListener('click', closeModal);
    modalConfirmButton.addEventListener('click', closeModal);
    
    logoutButton.addEventListener('click', (e) => {
        e.preventDefault();
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.close();
        }
        window.location.href = './main.html';
    });
    
    // 关闭WebSocket连接并清理资源
    window.addEventListener('beforeunload', () => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.close();
        }
    });
    
    // 按ESC键关闭模态框
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modalError.style.display === 'flex') {
            closeModal();
        }
    });
    
    // 初始化
    setDefaultDates();
    connectWebSocket();
    setLoading(false);
    exportReportButton.disabled = true;
    printReportButton.disabled = true;
});
