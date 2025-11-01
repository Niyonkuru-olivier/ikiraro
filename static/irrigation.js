// Chart for Irrigation Impact on Maize Productivity
const irrigationProductivityCtx = document.getElementById('irrigationProductivityChart').getContext('2d');
new Chart(irrigationProductivityCtx, {
    type: 'line',
    data: {
        labels: ['2020', '2021', '2022', '2023', '2024'],
        datasets: [{
            label: 'Productivity (tons per hectare)',
            data: [2.5, 3.0, 3.5, 4.0, 4.5], // Replace with actual data
            borderColor: 'rgba(75, 192, 192, 1)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            fill: true
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: false,
                title: {
                    display: true,
                    text: 'Productivity (tons per hectare)'
                }
            }
        },
        plugins: {
            title: {
                display: true,
                text: 'Impact of Irrigation on Maize Productivity'
            }
        }
    }
});
