// dashboard.js

// Maize and Beans yield data (2020-2024)
const maizeYieldData = [3.2, 3.5, 3.8, 4.1, 4.3]; // Maize yield in tonnes/hectare
const beansYieldData = [1.8, 2.0, 2.1, 2.3, 2.4]; // Beans yield in tonnes/hectare
const years = ['2020', '2021', '2022', '2023', '2024'];

// Chart configuration for Maize
const ctxMaize = document.getElementById('maizeYieldChart').getContext('2d');
const maizeChart = new Chart(ctxMaize, {
    type: 'line',
    data: {
        labels: years,
        datasets: [{
            label: 'Maize Yield (Tonnes/Hectare)',
            data: maizeYieldData,
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 2,
            fill: true,
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Yield (Tonnes/Hectare)'
                }
            }
        }
    }
});

// Chart configuration for Beans
const ctxBeans = document.getElementById('beansYieldChart').getContext('2d');
const beansChart = new Chart(ctxBeans, {
    type: 'line',
    data: {
        labels: years,
        datasets: [{
            label: 'Beans Yield (Tonnes/Hectare)',
            data: beansYieldData,
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 2,
            fill: true,
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Yield (Tonnes/Hectare)'
                }
            }
        }
    }
});

// Comments and analysis based on the yield data
const commentsSection = document.getElementById('dashboard-comments');

const analyzeYields = () => {
    let maizeYieldChange = maizeYieldData[maizeYieldData.length - 1] - maizeYieldData[0];
    let beansYieldChange = beansYieldData[beansYieldData.length - 1] - beansYieldData[0];

    let maizeTrend = maizeYieldChange > 0 ? 'increase' : 'decrease';
    let beansTrend = beansYieldChange > 0 ? 'increase' : 'decrease';

    let analysis = `
        From 2020 to 2024, maize yields have shown a ${maizeTrend} of ${maizeYieldChange.toFixed(2)} tonnes per hectare.
        Similarly, beans yields have experienced a ${beansTrend} of ${beansYieldChange.toFixed(2)} tonnes per hectare.
        Factors such as improved weather conditions, efficient use of fertilizers, and favorable government policies have contributed 
        to these positive trends. However, continued efforts are needed to address challenges such as climate variability and 
        access to modern farming tools.
    `;
    
    commentsSection.innerText = analysis;
};

// Run the analysis after the page loads
window.onload = analyzeYields;
