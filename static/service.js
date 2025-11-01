// Chart for Fertilizer Usage
const fertilizerUsageCtx = document.getElementById('fertilizerUsageChart').getContext('2d');
new Chart(fertilizerUsageCtx, {
    type: 'bar',
    data: {
        labels: ['NPK', 'DAP', 'Imborera'],
        datasets: [{
            label: 'Fertilizer Usage Rate (%)',
            data: [40, 30, 50],
            backgroundColor: ['rgba(75, 192, 192, 0.2)', 'rgba(255, 99, 132, 0.2)', 'rgba(153, 102, 255, 0.2)'],
            borderColor: ['rgba(75, 192, 192, 1)', 'rgba(255, 99, 132, 1)', 'rgba(153, 102, 255, 1)'],
            borderWidth: 1
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Usage Rate (%)'
                }
            }
        },
        plugins: {
            title: {
                display: true,
                text: 'Fertilizer Usage in Maize Farming'
            }
        }
    }
});

// Chart for Irrigation Impact on Yield
const irrigationImpactCtx = document.getElementById('irrigationImpactChart').getContext('2d');
new Chart(irrigationImpactCtx, {
    type: 'line',
    data: {
        labels: ['2020', '2021', '2022', '2023', '2024'],
        datasets: [{
            label: 'Yield (tons per hectare)',
            data: [2.5, 3.0, 3.5, 3.8, 4.0],
            borderColor: 'rgba(54, 162, 235, 1)',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            fill: true
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: false,
                title: {
                    display: true,
                    text: 'Yield (tons/hectare)'
                }
            }
        },
        plugins: {
            title: {
                display: true,
                text: 'Impact of Irrigation on Maize Yield'
            }
        }
    }
});

// JavaScript to track social media link clicks
document.querySelectorAll('.social-icons a').forEach((link) => {
  link.addEventListener('click', (event) => {
    const platform = event.target.closest('a').title;
    console.log(`User clicked on ${platform} link.`);
    alert(`Opening ${platform}!`);
  });
});
