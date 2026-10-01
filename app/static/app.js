// =============================================================================
// 전역 변수
// =============================================================================
let subscribers = [];
let currentDevices = [];
let selectedUserId = null;
let selectedDeviceId = null;
let usageChart = null;


// =============================================================================
// [요구사항 #3] 상태 기반 Badge 스타일
// =============================================================================
// TODO [요구사항 #3]: 상태 값(value)에 따라 적절한 CSS 클래스를 반환하세요.
//
function badgeClass(value) {
    const v = (value || "").toLowerCase();

    // 매핑 규칙:
    // Active, Online, Normal   → "badge status-active"   (초록)
    // Paused, Standby          → "badge status-paused"   (파랑)
    // Expired, Error, Warning  → "badge status-expired"  (빨강)
    // Offline                  → "badge status-offline"  (회색)
    // On, Cleaning             → "badge status-on"       (노랑)
    // Off                      → "badge status-off"      (연회색)
    // 그 외                     → "badge"
    return "badge";
}


// =============================================================================
// [요구사항 #1] 구독 사용자 조회 + 검색/필터
// =============================================================================

// TODO [요구사항 #1-A]: GET /api/subscribers 를 호출하여
//   subscribers 변수에 저장하고 renderSubscribers()를 호출하세요.
//
async function fetchSubscribers() {
    const response = await fetch("/api/subscribers");
    if (!response.ok) {
        console.error(`Failed to fetch subscribers: ${response.status}`);
        return;
    }
    subscribers = await response.json();
    renderSubscribers();
}

function renderSubscribers() {
    const tbody = document.getElementById("subscriber-body");
    const search = document.getElementById("subscriber-search").value.toLowerCase();
    const statusFilter = document.getElementById("subscriber-status-filter").value;

    const rows = document.createDocumentFragment();
    for (const subscriber of subscribers) {
        if (statusFilter && subscriber.status !== statusFilter) continue;
        if (![subscriber.name, subscriber.plan, subscriber.status, subscriber.userId]
            .some(value => String(value ?? "").toLowerCase().includes(search))) continue;

        const row = document.createElement("tr");
        row.classList.toggle("selected", subscriber.userId === selectedUserId);
        row.addEventListener("click", () => selectSubscriber(subscriber.userId));

        for (const field of ["userId", "name", "plan", "status", "deviceCount"]) {
            const cell = document.createElement("td");
            if (field === "status") {
                const badge = document.createElement("span");
                badge.className = badgeClass(subscriber.status);
                badge.textContent = subscriber.status ?? "";
                cell.appendChild(badge);
            } else {
                cell.textContent = subscriber[field] ?? "";
            }
            row.appendChild(cell);
        }
        rows.appendChild(row);
    }
    tbody.replaceChildren(rows);
}


// =============================================================================
// [요구사항 #2] 사용자별 가전 목록 + 사용 현황 + 차트
// =============================================================================

// TODO [요구사항 #2-A]: 사용자 클릭 시 해당 사용자의 가전 목록을 조회하세요.
//
async function selectSubscriber(userId) {
    selectedUserId = userId;
    selectedDeviceId = null;
    renderSubscribers();

    const usageEmpty = document.getElementById("usage-empty");
    usageEmpty.textContent = "Select a device to view usage details.";
    usageEmpty.classList.remove("hidden");
    document.getElementById("usage-detail").classList.add("hidden");
    document.getElementById("usage-info").replaceChildren();

    // 조회 중에는 이전 사용자의 가전 목록을 지운다 (이전 가전 클릭 방지)
    currentDevices = undefined;
    renderDevices();

    let devices = null;
    try {
        const response = await fetch(`/api/subscribers/${encodeURIComponent(userId)}/devices`);
        if (response.ok) {
            devices = await response.json();
        } else {
            console.error(`Failed to fetch devices: ${response.status}`);
        }
    } catch (error) {
        console.error("Failed to fetch devices:", error);
    }

    // 응답 대기 중 다른 사용자가 선택되었으면 이전 응답은 버린다
    if (userId !== selectedUserId) return;

    // null은 조회 실패를 의미 (renderDevices에서 실패 메시지 표시)
    currentDevices = Array.isArray(devices) ? devices : null;
    renderDevices();
}

// TODO [요구사항 #2-B]: currentDevices 배열을 테이블에 렌더링하세요.
//
function renderDevices() {
    const emptyEl = document.getElementById("device-empty");
    const tableEl = document.getElementById("device-table");
    const tbody = document.getElementById("device-body");
    const search = document.getElementById("device-search").value.toLowerCase();
    const statusFilter = document.getElementById("device-status-filter").value;

    let message = null;
    if (selectedUserId === null) message = "Select a subscriber to view devices.";
    else if (currentDevices === undefined) message = "Loading devices...";
    else if (currentDevices === null) message = "Failed to load devices.";
    else if (currentDevices.length === 0) message = "No registered devices";

    const filtered = message ? [] : currentDevices.filter(device =>
        (!statusFilter || device.status === statusFilter) &&
        [device.type, device.model, device.status, device.deviceId, device.location]
            .some(value => String(value ?? "").toLowerCase().includes(search)));
    if (!message && filtered.length === 0) message = "No devices matched";

    emptyEl.textContent = message ?? "";
    emptyEl.classList.toggle("hidden", !message);
    tableEl.classList.toggle("hidden", Boolean(message));

    const rows = document.createDocumentFragment();
    for (const device of filtered) {
        const row = document.createElement("tr");
        row.classList.toggle("selected", device.deviceId === selectedDeviceId);
        row.addEventListener("click", () => selectDevice(device.deviceId));

        for (const field of ["deviceId", "type", "model", "location", "status"]) {
            const cell = document.createElement("td");
            if (field === "status") {
                const badge = document.createElement("span");
                badge.className = badgeClass(device.status);
                badge.textContent = device.status ?? "";
                cell.appendChild(badge);
            } else {
                cell.textContent = device[field] ?? "";
            }
            row.appendChild(cell);
        }
        rows.appendChild(row);
    }
    tbody.replaceChildren(rows);
}

// TODO [요구사항 #2-C]: 가전 클릭 시 상세 사용 현황을 조회하세요.
//
async function selectDevice(deviceId) {
    selectedDeviceId = deviceId;
    renderDevices();

    let usage = null;
    try {
        const response = await fetch(`/api/devices/${encodeURIComponent(deviceId)}/usage`);
        if (response.ok) {
            usage = await response.json();
        } else {
            console.error(`Failed to fetch usage: ${response.status}`);
        }
    } catch (error) {
        console.error("Failed to fetch usage:", error);
    }

    // 응답 대기 중 다른 가전/사용자가 선택되었으면 이전 응답은 버린다
    if (deviceId !== selectedDeviceId) return;

    const usageEmpty = document.getElementById("usage-empty");
    const usageDetail = document.getElementById("usage-detail");
    if (!usage) {
        usageEmpty.textContent = "Failed to load usage details.";
        usageEmpty.classList.remove("hidden");
        usageDetail.classList.add("hidden");
        return;
    }
    usageEmpty.classList.add("hidden");
    usageDetail.classList.remove("hidden");

    // [label, value, badge 여부]
    const fields = [
        ["Device ID", usage.deviceId, false],
        ["Device Name", usage.deviceName, false],
        ["Power Status", usage.powerStatus, true],
        ["Last Used", usage.lastUsedAt, false],
        ["Total Usage Hours", usage.totalUsageHours, false],
        ["Weekly Usage Count", usage.weeklyUsageCount, false],
        ["Health Status", usage.healthStatus, true],
        ["Remark", usage.remark, false],
    ];
    const info = document.createDocumentFragment();
    for (const [label, value, isBadge] of fields) {
        const labelEl = document.createElement("div");
        labelEl.className = "label";
        labelEl.textContent = label;

        const valueEl = document.createElement("div");
        valueEl.className = "value";
        if (isBadge) {
            const badge = document.createElement("span");
            badge.className = badgeClass(value);
            badge.textContent = value ?? "";
            valueEl.appendChild(badge);
        } else {
            valueEl.textContent = value ?? "";
        }
        info.append(labelEl, valueEl);
    }
    document.getElementById("usage-info").replaceChildren(info);

    renderUsageChart(usage.weeklyUsageTrend ?? []);
}

// TODO [요구사항 #2-D]: Chart.js를 사용하여 주간 사용량 Bar Chart를 그리세요.
//
function renderUsageChart(trend) {
    const ctx = document.getElementById("usageChart");

    if (usageChart) usageChart.destroy();
    usageChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            datasets: [{
                label: "Weekly Usage Trend",
                data: trend,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: { y: { beginAtZero: true } }
        }
    });
}


// =============================================================================
// 이벤트 바인딩 + 초기화
// =============================================================================
function bindEvents() {
    document.getElementById("subscriber-search").addEventListener("input", renderSubscribers);
    document.getElementById("subscriber-status-filter").addEventListener("change", renderSubscribers);

    document.getElementById("device-search").addEventListener("input", renderDevices);
    document.getElementById("device-status-filter").addEventListener("change", renderDevices);
}

bindEvents();

fetchSubscribers();
