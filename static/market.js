// Sample price data for different regions and dates (for testing purposes)
const priceData = [
  { region: "Kigali", date: "2020", price: 300 },
  { region: "Kigali", date: "2021", price: 320 },
  { region: "Kigali", date: "2022", price: 350 },
  { region: "Kigali", date: "2023", price: 340 },
  { region: "Kigali", date: "2024", price: 370 },
  { region: "Eastern", date: "2020", price: 280 },
  { region: "Eastern", date: "2021", price: 310 },
  { region: "Eastern", date: "2022", price: 330 },
  { region: "Eastern", date: "2023", price: 350 },
  { region: "Eastern", date: "2024", price: 360 }
];

document.addEventListener("DOMContentLoaded", () => {
  initializeDashboard();
  const searchInput = document.getElementById("search");
  searchInput.addEventListener("keyup", event => {
    if (event.key === "Enter") {
      searchPrices();
    }
  });
});

function initializeDashboard() {
  renderDashboard(priceData);
  updateKpis();
  updateSearchHint(priceData.length, "");
  updateChartHint(priceData.length, "");
}

function searchPrices() {
  const query = document.getElementById("search").value.trim().toLowerCase();
  const filtered = priceData.filter(item =>
    item.region.toLowerCase().includes(query) || item.date.includes(query)
  );
  renderDashboard(filtered, query);
  updateSearchHint(filtered.length, query);
  updateChartHint(filtered.length, query);
}

function renderDashboard(dataset, query = "") {
  renderTable(dataset);
  drawChart(dataset);
  updateChartHint(dataset.length, query);
}

function renderTable(dataset) {
  const tbody = document.getElementById("prices-body");
  tbody.innerHTML = "";

  if (dataset.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td class="table-empty" colspan="3">
          No records match your filter. Try another year or region.
        </td>
      </tr>
    `;
    return;
  }

  const sorted = [...dataset].sort((a, b) => Number(a.date) - Number(b.date));
  sorted.forEach(item => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${item.region}</td>
      <td>${item.date}</td>
      <td>${item.price.toLocaleString()} RWF</td>
    `;
    tbody.appendChild(row);
  });
}

function drawChart(dataset) {
  const ctx = document.getElementById("price-chart").getContext("2d");
  if (window.priceChart) {
    window.priceChart.destroy();
    window.priceChart = null;
  }

  if (!dataset.length) {
    return;
  }

  const labels = [...new Set(dataset.map(item => item.date))].sort();
  const regions = [...new Set(dataset.map(item => item.region))];
  const palette = ["#5AE4A7", "#33B1FF", "#F9A826", "#915BFF"];

  const datasets = regions.map((region, index) => {
    const dataPoints = labels.map(label => {
      const match = dataset.find(item => item.region === region && item.date === label);
      return match ? match.price : null;
    });
    return {
      label: `${region} price`,
      data: dataPoints,
      tension: 0.35,
      borderColor: palette[index % palette.length],
      backgroundColor: `${palette[index % palette.length]}33`,
      borderWidth: 2,
      fill: true,
      spanGaps: true
    };
  });

  window.priceChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: true,
          position: "bottom",
          labels: {
            color: "#f0fff4"
          }
        },
        tooltip: {
          mode: "index",
          intersect: false,
          backgroundColor: "#03140b",
          titleColor: "#ffffff",
          bodyColor: "#c9ffe3",
          borderColor: "#4caf50",
          borderWidth: 1
        }
      },
      interaction: {
        mode: "nearest",
        axis: "x",
        intersect: false
      },
      scales: {
        y: {
          beginAtZero: false,
          grid: {
            color: "rgba(255,255,255,0.08)"
          },
          ticks: {
            color: "#dfeee3",
            callback: value => `${value} RWF`
          },
          title: {
            display: true,
            text: "Price (RWF)",
            color: "#dfeee3"
          }
        },
        x: {
          grid: {
            color: "rgba(255,255,255,0.05)"
          },
          ticks: {
            color: "#dfeee3"
          },
          title: {
            display: true,
            text: "Year",
            color: "#dfeee3"
          }
        }
      }
    }
  });
}

function updateKpis() {
  const kigali = summarizeRegion("Kigali");
  const eastern = summarizeRegion("Eastern");

  document.getElementById("kigali-latest").textContent = formatPrice(kigali.latest.price);
  document.getElementById("eastern-latest").textContent = formatPrice(eastern.latest.price);

  document.getElementById("kigali-trend").textContent = formatYoY(kigali.latest.price, kigali.previous.price);
  document.getElementById("eastern-trend").textContent = formatYoY(eastern.latest.price, eastern.previous.price);

  const spread = kigali.latest.price - eastern.latest.price;
  document.getElementById("price-spread").textContent = `${spread >= 0 ? "+" : ""}${spread.toLocaleString()} RWF`;
}

function summarizeRegion(region) {
  const series = priceData.filter(item => item.region === region);
  const latest = series.reduce((acc, cur) => Number(cur.date) > Number(acc.date) ? cur : acc);
  const previous = series
    .filter(item => Number(item.date) === Number(latest.date) - 1)[0] || series[series.length - 2] || latest;
  return { latest, previous };
}

function formatPrice(value) {
  return `${value.toLocaleString()} RWF`;
}

function formatYoY(current, previous) {
  if (!previous) return "No prior year to compare.";
  const change = current - previous;
  const pct = ((change / previous) * 100).toFixed(1);
  const direction = change >= 0 ? "Up" : "Down";
  return `${direction} ${Math.abs(change).toLocaleString()} RWF versus last year (${Math.abs(pct)}% change).`;
}

function updateSearchHint(count, query) {
  const hint = document.getElementById("search-hint");
  if (!query) {
    hint.textContent = "Showing the complete 2020-2024 dataset.";
    return;
  }
  hint.textContent = count
    ? `Found ${count} row(s) for "${query}".`
    : `Nothing matches "${query}". Clear the filter or try another year/region.`;
}

function updateChartHint(count, query) {
  const chartHint = document.getElementById("chart-hint");
  if (!chartHint) return;
  if (!count) {
    chartHint.textContent = query
      ? `No chart data for "${query}". Clear the filter to bring back the full view.`
      : "No chart data available. Please adjust the dataset.";
    return;
  }

  chartHint.textContent = query
    ? `Chart filtered by "${query}". Hover or tap to compare both regions for the same year.`
    : "Hover or tap to see Kigali and Eastern Province prices for the same year.";
}
