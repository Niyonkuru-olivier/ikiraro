// Chart.js integration for drawing the graphs
document.addEventListener("DOMContentLoaded", function() {
    drawInitialCharts();
});

let priceChart;  // Declare the price chart variable

function drawInitialCharts() {
    // Maize Price Chart (Initial Graph for full range 2020-2024)
    const priceCtx = document.getElementById('priceChart').getContext('2d');
    priceChart = new Chart(priceCtx, {
        type: 'line',
        data: {
            labels: [2020, 2021, 2022, 2023, 2024],
            datasets: [{
                label: 'Price (USD per kg)',
                data: [0.40, 0.35, 0.36, 0.33, 0.34],
                borderColor: 'green',
                fill: false
            }]
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Maize Prices (2020-2024)'
            }
        }
    });

    // Maize Demand Chart
    const demandCtx = document.getElementById('demandChart').getContext('2d');
    new Chart(demandCtx, {
        type: 'line',
        data: {
            labels: [2020, 2021, 2022, 2023, 2024],
            datasets: [{
                label: 'Demand (Thousand Tonnes)',
                data: [600, 620, 650, 680, 700],
                borderColor: 'blue',
                fill: false
            }]
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Maize Demand (2020-2024)'
            }
        }
    });

    // Market Trends Chart
    const trendsCtx = document.getElementById('trendsChart').getContext('2d');
    new Chart(trendsCtx, {
        type: 'line',
        data: {
            labels: [2020, 2021, 2022, 2023, 2024],
            datasets: [{
                label: 'Market Trends (% Change)',
                data: [5, 8, 10, 7, 9],
                borderColor: 'orange',
                fill: false
            }]
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Maize Market Trends (2020-2024)'
            }
        }
    });
}

// Function to update the price chart based on selected year range
function drawPriceChange() {
    const startYear = parseInt(document.getElementById('startYear').value);
    const endYear = parseInt(document.getElementById('endYear').value);
    
    const allYears = [2020, 2021, 2022, 2023, 2024];
    const allPrices = [0.40, 0.35, 0.36, 0.33, 0.34];  // Prices for full range

    // Get the index range for the selected years
    const startIndex = allYears.indexOf(startYear);
    const endIndex = allYears.indexOf(endYear) + 1;  // End is inclusive

    // Slice the years and prices for the selected range
    const selectedYears = allYears.slice(startIndex, endIndex);
    const selectedPrices = allPrices.slice(startIndex, endIndex);

    // Update the price chart with new data
    priceChart.data.labels = selectedYears;
    priceChart.data.datasets[0].data = selectedPrices;
    priceChart.update();
}
