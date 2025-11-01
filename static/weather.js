// Example data for the chart
const ctx = document.getElementById('cropYieldChart').getContext('2d');
const cropYieldChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['2018', '2019', '2020', '2021', '2022'],
        datasets: [{
            label: 'Crop Yield (tons)',
            data: [1.5, 2.0, 2.5, 3.0, 3.5],
            borderColor: 'rgba(76, 175, 80, 1)',
            backgroundColor: 'rgba(76, 175, 80, 0.2)',
            borderWidth: 2,
            fill: true
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});
