/* dashboard.js — Dashboard Data & Charts */

// ═══ MOCK DATA ═══
const months = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'];

const hatchData2026 = [4820, 7310, 9100, 11200, 13450, 15800, 18200, 19600, 21400, null, null, null];
const hatchData2025 = [2100, 3800, 5400, 7200, 9000, 11500, 13200, 15000, 16800, 18200, 19800, 21500];

const speciesData = {
  labels: ['Ayam', 'Puyuh', 'Bebek', 'Angsa', 'Kalkun'],
  data: [52, 24, 15, 6, 3],
  colors: ['#D97706', '#8B5CF6', '#3B82F6', '#475569', '#92400E'],
  bgColors: ['rgba(217,119,6,0.85)', 'rgba(139,92,246,0.85)', 'rgba(59,130,246,0.85)', 'rgba(71,85,105,0.85)', 'rgba(146,64,14,0.85)'],
};

const provinceData = {
  labels: ['Jawa Timur','Jawa Tengah','Jawa Barat','Sumatera Utara','Sulawesi Selatan','Kalimantan Timur','Lampung','Bali','NTB','DIY Yogyakarta'],
  data: [624, 518, 487, 312, 268, 195, 178, 142, 121, 98],
};

const successRateData = [78.2, 80.1, 81.5, 82.3, 83.8, 84.2, 85.5, 85.9, 86.7, 86.4, 87.1, 87.3];

const growthData = [210, 324, 485, 643, 812, 1020, 1248, 1512, 1789, null, null, null];

// ═══ FARMER TABLE DATA ═══
const names = ['Budi Santoso','Siti Rahayu','Ahmad Hidayat','Dewi Kurnia','Hendra Wijaya','Rina Marlina','Joko Purnomo','Ani Sulistya','Fajar Nugroho','Endang Wati','Sugeng Raharjo','Fitri Handayani','Bambang Saputra','Lestari Utami','Eko Prasetyo','Nurul Aini','Hendro Kusuma','Ratna Sari','Agus Santoso','Sri Wahyuni'];
const locs = ['Blitar, Jatim','Yogyakarta, DIY','Brebes, Jateng','Malang, Jatim','Medan, Sumut','Bandung, Jabar','Surabaya, Jatim','Makassar, Sulsel','Semarang, Jateng','Solo, Jateng','Banyumas, Jateng','Garut, Jabar','Kediri, Jatim','Klaten, Jateng','Jember, Jatim','Sidoarjo, Jatim','Tulungagung, Jatim','Ponorogo, Jatim','Madiun, Jatim','Batu, Jatim'];
const species = ['Ayam','Puyuh','Bebek','Ayam','Angsa','Kalkun','Ayam','Puyuh','Bebek','Ayam','Puyuh','Ayam','Bebek','Kalkun','Ayam','Puyuh','Angsa','Ayam','Bebek','Ayam'];
// SVG icons untuk setiap jenis hewan (inline, tidak pakai emoji)
const speciesSVG = {
  Ayam: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;margin-right:4px"><ellipse cx="12" cy="14" rx="6" ry="7" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="6" r="3" stroke="currentColor" stroke-width="2"/><path d="M15 5l2-2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M8 18l-2 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M16 18l2 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
  Puyuh: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;margin-right:4px"><ellipse cx="12" cy="15" rx="5" ry="6" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="7" r="3" stroke="currentColor" stroke-width="2"/><path d="M9 20l-1 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M15 20l1 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
  Bebek: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;margin-right:4px"><ellipse cx="12" cy="14" rx="7" ry="6" stroke="currentColor" stroke-width="2"/><circle cx="8" cy="7" r="3" stroke="currentColor" stroke-width="2"/><path d="M11 6h4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M9 19l-1 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M15 19l1 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
  Angsa: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;margin-right:4px"><ellipse cx="12" cy="16" rx="6" ry="5" stroke="currentColor" stroke-width="2"/><path d="M12 11 Q10 6 12 3 Q16 2 17 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/><path d="M9 20l-1 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M15 20l1 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
  Kalkun: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;margin-right:4px"><ellipse cx="12" cy="14" rx="6" ry="7" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="5" r="3" stroke="currentColor" stroke-width="2"/><path d="M9 3 Q6 0 5 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" fill="none"/><path d="M9 20l-1 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M15 20l1 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
};
const locationSVG = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;margin-right:3px"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="9" r="2.5" stroke="currentColor" stroke-width="2"/></svg>`;
const statuses = ['Aktif','Aktif','Aktif','Menunggu','Aktif','Selesai','Aktif','Aktif','Menunggu','Aktif'];

function genFarmers(count) {
  return Array.from({ length: count }, (_, i) => {
    const total = 20 + Math.floor(Math.random() * 200);
    const rate  = 0.7 + Math.random() * 0.28;
    const hatched = Math.round(total * rate);
    return {
      name:    names[i % names.length],
      farm:    `Peternakan ${names[i % names.length].split(' ')[0]}`,
      loc:     locs[i % locs.length],
      species: species[i % species.length],
      total,
      hatched,
      rate:    Math.round(rate * 100),
      status:  statuses[i % statuses.length],
    };
  });
}

const allFarmers = genFarmers(50);
let filteredFarmers = [...allFarmers];

// ═══ CHART INSTANCES ═══
let hatchChart, speciesChart, provinceChart, successChart, growthChart;

// ═══ CHART DEFAULTS ═══
Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
Chart.defaults.color = '#5A6B5C';

function commonTooltip() {
  return {
    backgroundColor: 'rgba(26,43,28,0.92)',
    titleColor: '#fff',
    bodyColor: 'rgba(255,255,255,0.75)',
    borderColor: 'rgba(82,201,127,0.3)',
    borderWidth: 1,
    cornerRadius: 10,
    padding: 12,
  };
}

// ═══ INIT CHARTS ═══
function initHatchChart() {
  const ctx = document.getElementById('hatchChart');
  if (!ctx) return;
  if (hatchChart) hatchChart.destroy();

  const data = hatchData2026.filter(v => v !== null);
  const labels = months.slice(0, data.length);

  hatchChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Telur Menetas',
        data,
        backgroundColor: labels.map((_, i) =>
          i === data.length - 1
            ? 'rgba(47,107,63,0.9)'
            : 'rgba(47,107,63,0.4)'
        ),
        borderColor: 'rgba(47,107,63,1)',
        borderWidth: 0,
        borderRadius: 8,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          ...commonTooltip(),
          callbacks: {
            label: ctx => `  ${ctx.parsed.y.toLocaleString('id-ID')} telur`,
          }
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { callback: v => v.toLocaleString('id-ID') },
        },
        x: { grid: { display: false } },
      },
    },
  });
}

function initSpeciesChart() {
  const ctx = document.getElementById('speciesChart');
  if (!ctx) return;
  if (speciesChart) speciesChart.destroy();

  speciesChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: speciesData.labels,
      datasets: [{
        data: speciesData.data,
        backgroundColor: speciesData.bgColors,
        borderColor: '#fff',
        borderWidth: 3,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true,
      cutout: '65%',
      plugins: {
        legend: { display: false },
        tooltip: {
          ...commonTooltip(),
          callbacks: {
            label: ctx => `  ${ctx.parsed}% inkubator aktif`,
          }
        },
      },
    },
  });

  // Custom legend
  const legend = document.getElementById('speciesLegend');
  if (legend) {
    legend.innerHTML = speciesData.labels.map((l, i) => `
      <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;">
        <span style="width:10px;height:10px;border-radius:3px;background:${speciesData.bgColors[i]};flex-shrink:0;"></span>
        <span style="color:var(--text-muted);">${l}</span>
        <span style="font-weight:700;margin-left:auto;">${speciesData.data[i]}%</span>
      </div>
    `).join('');
  }
}

function initProvinceChart() {
  const ctx = document.getElementById('provinceChart');
  if (!ctx) return;
  if (provinceChart) provinceChart.destroy();

  provinceChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: provinceData.labels,
      datasets: [{
        label: 'Jumlah Peternak',
        data: provinceData.data,
        backgroundColor: 'rgba(47,107,63,0.7)',
        borderColor: 'rgba(47,107,63,1)',
        borderWidth: 0,
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          ...commonTooltip(),
          callbacks: {
            label: ctx => `  ${ctx.parsed.x} peternak`,
          }
        },
      },
      scales: {
        x: {
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.04)' },
        },
        y: { grid: { display: false } },
      },
    },
  });
}

function initSuccessChart() {
  const ctx = document.getElementById('successRateChart');
  if (!ctx) return;
  if (successChart) successChart.destroy();

  successChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: months,
      datasets: [{
        label: 'Tingkat Keberhasilan (%)',
        data: successRateData,
        borderColor: '#2F6B3F',
        backgroundColor: 'rgba(47,107,63,0.08)',
        pointBackgroundColor: '#2F6B3F',
        pointRadius: 5,
        pointHoverRadius: 7,
        borderWidth: 2.5,
        fill: true,
        tension: 0.4,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          ...commonTooltip(),
          callbacks: {
            label: ctx => `  ${ctx.parsed.y}% keberhasilan`,
          }
        },
      },
      scales: {
        y: {
          min: 70, max: 100,
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { callback: v => v + '%' },
        },
        x: { grid: { display: false } },
      },
    },
  });
}

function initGrowthChart() {
  const ctx = document.getElementById('growthChart');
  if (!ctx) return;
  if (growthChart) growthChart.destroy();

  const data = growthData.filter(v => v !== null);
  const labels = months.slice(0, data.length);

  growthChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Peternak Terdaftar',
        data,
        borderColor: '#8B5CF6',
        backgroundColor: 'rgba(139,92,246,0.08)',
        pointBackgroundColor: '#8B5CF6',
        pointRadius: 5,
        borderWidth: 2.5,
        fill: true,
        tension: 0.4,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          ...commonTooltip(),
          callbacks: {
            label: ctx => `  ${ctx.parsed.y.toLocaleString('id-ID')} peternak`,
          }
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { callback: v => v.toLocaleString('id-ID') },
        },
        x: { grid: { display: false } },
      },
    },
  });
}

// ═══ UPDATE CHARTS ═══
function updateHatchChart(year) {
  if (!hatchChart) return;
  const data = year === '2025' ? hatchData2025 : hatchData2026.filter(v => v !== null);
  const labels = months.slice(0, data.length);
  hatchChart.data.labels = labels;
  hatchChart.data.datasets[0].data = data;
  hatchChart.data.datasets[0].backgroundColor = labels.map((_, i) =>
    i === data.length - 1 ? 'rgba(47,107,63,0.9)' : 'rgba(47,107,63,0.4)'
  );
  hatchChart.update();
}

// ═══ FARMER TABLE ═══
function renderFarmerTable(farmers, tbodyId = 'farmerTable', limit = 10) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  tbody.innerHTML = farmers.slice(0, limit).map((f, i) => `
    <tr>
      <td>
        <div class="table-name-row">
          <div class="table-avatar">${f.name.split(' ').map(n=>n[0]).join('').slice(0,2)}</div>
          <div>
            <div class="table-name">${f.name}</div>
            <div class="table-farm">${f.farm}</div>
          </div>
        </div>
      </td>
      <td style="color:var(--text-muted); font-size:0.8125rem;">${f.loc}</td>
      <td>${f.species}</td>
      <td><span class="status-dot ${f.status === 'Aktif' ? 'status-active' : f.status === 'Selesai' ? 'status-done' : 'status-waiting'}">${f.status}</span></td>
      <td style="font-weight:700; color:var(--green-primary);">${f.hatched.toLocaleString('id-ID')}</td>
    </tr>
  `).join('');
}

function renderFullFarmerTable(farmers) {
  const tbody = document.getElementById('fullFarmerBody');
  if (!tbody) return;
  tbody.innerHTML = farmers.map((f, i) => `
    <tr>
      <td style="color:var(--text-muted); font-size:0.8125rem; font-weight:600;">${String(i+1).padStart(2,'0')}</td>
      <td>
        <div class="table-name-row">
          <div class="table-avatar" style="width:28px;height:28px;font-size:0.65rem;">${f.name.split(' ').map(n=>n[0]).join('').slice(0,2)}</div>
          <div>
            <div class="table-name" style="font-size:0.875rem;">${f.name}</div>
            <div class="table-farm">${f.farm}</div>
          </div>
        </div>
      </td>
      <td style="color:var(--text-muted); font-size:0.8125rem;">${f.loc}</td>
      <td>${f.species}</td>
      <td style="font-weight:600;">${f.total.toLocaleString('id-ID')}</td>
      <td style="font-weight:700; color:var(--green-primary);">${f.hatched.toLocaleString('id-ID')}</td>
      <td>
        <div style="display:flex; align-items:center; gap:8px;">
          <div style="flex:1; height:6px; background:var(--bg); border-radius:3px; overflow:hidden; min-width:60px;">
            <div style="height:100%; width:${f.rate}%; background:${f.rate >= 85 ? '#22C55E' : f.rate >= 70 ? '#F59E0B' : '#EF4444'}; border-radius:3px;"></div>
          </div>
          <span style="font-size:0.75rem; font-weight:700; color:${f.rate >= 85 ? '#16A34A' : f.rate >= 70 ? '#B45309' : '#DC2626'};">${f.rate}%</span>
        </div>
      </td>
      <td><span class="status-dot ${f.status === 'Aktif' ? 'status-active' : f.status === 'Selesai' ? 'status-done' : 'status-waiting'}">${f.status}</span></td>
    </tr>
  `).join('');
}

function filterFarmers() {
  const q = document.getElementById('farmerSearch')?.value.toLowerCase() || '';
  filteredFarmers = allFarmers.filter(f =>
    f.name.toLowerCase().includes(q) ||
    f.loc.toLowerCase().includes(q) ||
    f.species.toLowerCase().includes(q)
  );
  renderFullFarmerTable(filteredFarmers);
}

function filterBySpecies(sp) {
  filteredFarmers = sp ? allFarmers.filter(f => f.species === sp) : [...allFarmers];
  renderFullFarmerTable(filteredFarmers);
}

// ═══ LIVE FEED ═══
const liveIncubators = [
  { name: 'Inkubator Ayam #1', owner: 'Budi Santoso', temp: 37.6, humid: 61, day: 14, total: 21, status: 'online', species: 'Ayam' },
  { name: 'Inkubator Puyuh #3', owner: 'Siti Rahayu', temp: 37.9, humid: 58, day: 9, total: 17, status: 'online', species: 'Puyuh' },
  { name: 'Inkubator Bebek #2', owner: 'Ahmad Hidayat', temp: 37.3, humid: 72, day: 22, total: 28, status: 'warning', species: 'Bebek' },
  { name: 'Inkubator Ayam #5', owner: 'Dewi Kurnia', temp: 37.7, humid: 63, day: 3, total: 21, status: 'online', species: 'Ayam' },
  { name: 'Inkubator Angsa #1', owner: 'Hendra Wijaya', temp: 37.1, humid: 68, day: 18, total: 30, status: 'online', species: 'Angsa' },
  { name: 'Inkubator Puyuh #7', owner: 'Rina Marlina', temp: 0, humid: 0, day: 5, total: 17, status: 'offline', species: 'Puyuh' },
];

function renderLiveFeed() {
  const feed = document.getElementById('liveFeed');
  if (!feed) return;
  feed.innerHTML = liveIncubators.slice(0, 5).map(inc => `
    <div class="live-item">
      <div class="live-dot ${inc.status !== 'online' ? 'offline' : ''}"></div>
      <div class="live-info">
        <div class="live-name">${inc.name}</div>
        <div class="live-meta">${inc.owner} · Hari ${inc.day}/${inc.total}</div>
      </div>
      <div class="live-temp" style="color:${inc.status === 'offline' ? '#94A3B8' : inc.temp > 38.5 ? '#EF4444' : '#EF4444'};">
        ${inc.status === 'offline' ? '—' : `${inc.temp}°C`}
      </div>
    </div>
  `).join('');
}

function renderLiveGrid() {
  const grid = document.getElementById('liveIncubatorGrid');
  if (!grid) return;
  grid.innerHTML = liveIncubators.map(inc => `
    <div class="chart-card card-hover" style="padding:20px;">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px;">
        <div>
          <div style="font-weight:700; font-size:0.9375rem;">${inc.name}</div>
          <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">${inc.owner}</div>
        </div>
        <span class="status-dot ${inc.status === 'online' ? 'status-active' : inc.status === 'warning' ? 'status-waiting' : ''}" style="font-size:0.7rem;">
          ${inc.status === 'online' ? 'Online' : inc.status === 'warning' ? 'Perhatian' : 'Offline'}
        </span>
      </div>

      <div style="display:flex; gap:10px; margin-bottom:14px;">
        <div style="flex:1; background:rgba(239,68,68,0.08); border-radius:12px; padding:12px; text-align:center; border:1px solid rgba(239,68,68,0.1);">
          <div style="font-size:1.375rem; font-weight:800; color:${inc.status==='offline' ? '#94A3B8' : '#EF4444'};">
            ${inc.status === 'offline' ? '—' : inc.temp + '°C'}
          </div>
          <div style="font-size:0.7rem; color:var(--text-muted); margin-top:2px;">Suhu</div>
        </div>
        <div style="flex:1; background:rgba(59,130,246,0.08); border-radius:12px; padding:12px; text-align:center; border:1px solid rgba(59,130,246,0.1);">
          <div style="font-size:1.375rem; font-weight:800; color:${inc.status==='offline' ? '#94A3B8' : '#3B82F6'};">
            ${inc.status === 'offline' ? '—' : inc.humid + '%'}
          </div>
          <div style="font-size:0.7rem; color:var(--text-muted); margin-top:2px;">Kelembaban</div>
        </div>
      </div>

      <div style="margin-bottom:8px; display:flex; justify-content:space-between; font-size:0.75rem; color:var(--text-muted);">
        <span>${inc.species}</span>
        <span>Hari ${inc.day}/${inc.total}</span>
      </div>
      <div style="height:6px; background:var(--bg); border-radius:3px; overflow:hidden;">
        <div style="height:100%; width:${Math.round(inc.day/inc.total*100)}%; background:linear-gradient(to right, var(--green-primary), var(--green-light)); border-radius:3px; transition:width 0.5s;"></div>
      </div>
    </div>
  `).join('');
}

// ═══ LIVE SENSOR SIMULATION ═══
function simulateSensors() {
  liveIncubators.forEach(inc => {
    if (inc.status !== 'offline') {
      inc.temp = Math.round((inc.temp + (Math.random() - 0.5) * 0.4) * 10) / 10;
      inc.temp = Math.max(36.5, Math.min(38.5, inc.temp));
      inc.humid = Math.round(inc.humid + (Math.random() - 0.5) * 2);
      inc.humid = Math.max(55, Math.min(85, inc.humid));
    }
  });
  renderLiveFeed();
  renderLiveGrid();
}

// ═══ PAGE NAVIGATION ═══
const pages = ['overview', 'peternak', 'inkubator', 'statistik'];
const pageTitles = {
  overview: 'Overview Dashboard',
  peternak: 'Data Peternak',
  inkubator: 'Inkubator Live',
  statistik: 'Statistik & Analitik',
};

function showPage(page) {
  pages.forEach(p => {
    const el = document.getElementById(`page-${p}`);
    if (el) el.style.display = p === page ? 'block' : 'none';
  });

  document.querySelectorAll('.nav-item').forEach((el, i) => {
    el.classList.remove('active');
  });

  // Set active nav
  document.querySelectorAll('.nav-item').forEach(el => {
    if (el.getAttribute('onclick') === `showPage('${page}')`) {
      el.classList.add('active');
    }
  });

  document.getElementById('pageTitle').textContent = pageTitles[page] || page;

  if (page === 'peternak') {
    renderFullFarmerTable(allFarmers);
  }
  if (page === 'inkubator') {
    renderLiveGrid();
  }
  if (page === 'statistik') {
    setTimeout(() => {
      initSuccessChart();
      initGrowthChart();
    }, 100);
  }
}

// ═══ SIDEBAR TOGGLE ═══
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// ═══ REFRESH ═══
function refreshData() {
  simulateSensors();
  const btn = document.querySelector('[onclick="refreshData()"]');
  if (btn) {
    btn.style.transform = 'rotate(360deg)';
    btn.style.transition = 'transform 0.6s';
    setTimeout(() => { btn.style.transform = ''; btn.style.transition = ''; }, 700);
  }
}

// ═══ TOPBAR DATE ═══
function updateDate() {
  const el = document.getElementById('topbarDate');
  if (el) {
    el.textContent = new Date().toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  }
}

// ═══ METRIC COUNTER ANIMATION ═══
function animateCount(el, target, duration = 1800) {
  if (el._counted) return;
  el._counted = true;
  const step = (ts) => {
    if (!el._st) el._st = ts;
    const p = Math.min((ts - el._st) / duration, 1);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(eased * target).toLocaleString('id-ID');
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// ═══ INIT ═══
document.addEventListener('DOMContentLoaded', () => {
  updateDate();
  renderFarmerTable(allFarmers);
  renderLiveFeed();

  setTimeout(() => {
    initHatchChart();
    initSpeciesChart();
    initProvinceChart();

    // Animate metric counters
    document.querySelectorAll('[data-count]').forEach(el => {
      const target = parseInt(el.dataset.count);
      animateCount(el, target);
    });
  }, 200);

  // Live sensor updates every 5s
  setInterval(simulateSensors, 5000);
});
