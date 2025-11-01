// dashboard.js

// Crop yield data (example for Maize and Beans in tons over the years)
const cropYieldData = {
    labels: ['2020', '2021', '2022', '2023', '2024'],
    datasets: [
        {
            label: 'Maize Yield',
            data: [250, 300, 280, 320, 350],
            backgroundColor: '#4CAF50',
            borderColor: '#388E3C',
            borderWidth: 1
        },
        {
            label: 'Beans Yield',
            data: [200, 220, 230, 210, 240],
            backgroundColor: '#FF9800',
            borderColor: '#F57C00',
            borderWidth: 1
        }
    ]
};

// Bar chart configuration for crop yield
const ctxYield = document.getElementById('cropYieldChart').getContext('2d');
const cropYieldChart = new Chart(ctxYield, {
    type: 'bar',
    data: cropYieldData,
    options: {
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Yield in Tons'
                }
            }
        },
        plugins: {
            legend: {
                display: true
            }
        }
    }
});

// Fertilizer usage data
const fertilizerData = {
    labels: ['2020', '2021', '2022', '2023', '2024'],
    datasets: [
        {
            label: 'Fertilizer Use (Tons)',
            data: [100, 120, 140, 160, 180],
            backgroundColor: '#2196F3',
            borderColor: '#1976D2',
            borderWidth: 1
        }
    ]
};

// Line chart for fertilizer usage
const ctxFertilizer = document.getElementById('fertilizerChart').getContext('2d');
const fertilizerChart = new Chart(ctxFertilizer, {
    type: 'line',
    data: fertilizerData,
    options: {
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Fertilizer Use (Tons)'
                }
            }
        }
    }
});

// Weather data (average rainfall in mm)
const weatherData = {
    labels: ['2020', '2021', '2022', '2023', '2024'],
    datasets: [
        {
            label: 'Average Rainfall (mm)',
            data: [800, 900, 850, 880, 920],
            backgroundColor: '#FFC107',
            borderColor: '#FFA000',
            borderWidth: 1
        }
    ]
};

// Line chart for weather data
const ctxWeather = document.getElementById('weatherChart').getContext('2d');
const weatherChart = new Chart(ctxWeather, {
    type: 'line',
    data: weatherData,
    options: {
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Rainfall (mm)'
                }
            }
        }
    }
});

// Government policy impact (percentage)
const policyData = {
    labels: ['2020', '2021', '2022', '2023', '2024'],
    datasets: [
        {
            label: 'Policy Impact on Yield (%)',
            data: [15, 20, 18, 22, 25],
            backgroundColor: '#9C27B0',
            borderColor: '#7B1FA2',
            borderWidth: 1
        }
    ]
};

// Pie chart for policy impact
const ctxPolicy = document.getElementById('policyImpactChart').getContext('2d');
const policyImpactChart = new Chart(ctxPolicy, {
    type: 'pie',
    data: policyData,
    options: {
        responsive: true
    }
});
