// dashboard.js

// Data for factors impacting crop yields (example data in percentage of impact)
const factorsData = {
    labels: ['Weather', 'Fertilizer Use', 'Government Policy', 'Land Form', 'Irrigation', 'Climate Change', 'Low Prices', 'Pests/Disease', 'Thieves'],
    datasets: [{
        label: 'Impact on Yield (%)',
        data: [40, 30, 20, 10, 60, 15, 12, 8, 5], // Example percentages
        backgroundColor: [
            '#4CAF50', '#2196F3', '#FFC107', '#FF5722', '#009688', '#FF9800', '#795548', '#9C27B0', '#E91E63'
        ],
        borderWidth: 1
    }]
};

// Bar chart configuration
const ctxFactors = document.getElementById('factorsChart').getContext('2d');
const factorsChart = new Chart(ctxFactors, {
    type: 'bar',
    data: factorsData,
    options: {
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Impact on Yield (%)'
                }
            }
        },
        plugins: {
            legend: {
                display: false
            }
        }
    }
});

// Comments and analysis on the factors
const commentsSection = document.getElementById('dashboard-comments');

const analyzeFactors = () => {
    let highestImpact = Math.max(...factorsData.datasets[0].data);
    let highestFactor = factorsData.labels[factorsData.datasets[0].data.indexOf(highestImpact)];
    
    let analysis = `
        The factor with the highest impact on crop yields between 2020 and 2024 is ${highestFactor} with an impact rate of ${highestImpact}%.
        This suggests that ${highestFactor} has had the most significant effect on both maize and beans yields in Rwanda, indicating 
        the need for further improvements in this area.
    `;
    
    commentsSection.innerText = analysis;
};

// Run the analysis after the page loads
window.onload = analyzeFactors;
