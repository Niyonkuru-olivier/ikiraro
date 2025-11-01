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

// Function to display search results in a table
function searchPrices() {
  const searchQuery = document.getElementById("search").value.toLowerCase();
  const filteredData = priceData.filter(item =>
    item.region.toLowerCase().includes(searchQuery) || item.date.includes(searchQuery)
  );

  const table = document.getElementById("prices-table");
  table.innerHTML = `
    <tr>
      <th>Region</th>
      <th>Date</th>
      <th>Price (RWF)</th>
    </tr>
  `;

  filteredData.forEach(item => {
    const row = `
      <tr>
        <td>${item.region}</td>
        <td>${item.date}</td>
        <td>${item.price}</td>
      </tr>
    `;
    table.innerHTML += row;
  });

  if (filteredData.length > 0) {
    const labels = filteredData.map(item => item.date);
    const prices = filteredData.map(item => item.price);
    drawChart(labels, prices);
  } else {
    drawChart([], []);
  }
}

// Function to draw the chart using Chart.js
function drawChart(labels, data) {
  const ctx = document.getElementById('price-chart').getContext('2d');
  if (window.priceChart) {
    window.priceChart.destroy(); // Destroy existing chart before creating a new one
  }
  window.priceChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Maize Price (RWF)',
        data: data,
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        fill: true
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: false,
          title: {
            display: true,
            text: 'Price (RWF)'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Year'
          }
        }
      }
    }
  });
}
