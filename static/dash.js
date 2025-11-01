// Sample Data (Replace with dynamic data)
const districts = ['Rwamagana', 'Kayonza'];
const totalSpent = [617388710, 632886700];
const avokaQtyPlanted = [2000, 1800, 1500, 1300];
const farmerGroups = ['TUZAMURANE', 'TWITEZIMBERE', 'DUTERIMBERE', 'ICYEREKEZO', 'ABISHYIZEHAMWE'];
const totalExpenses2024 = [50, 45, 42, 39, 35];
const inkokoQtyOrdered = [29522, 17828];

// Avoka Qty Planted (Bar Chart)
const ctx1 = document.getElementById('avokaQtyChart').getContext('2d');
new Chart(ctx1, {
    type: 'bar',
    data: {
        labels: ['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5'],
        datasets: [{
            label: 'AvokaQty Planted in 2024',
            data: avokaQtyPlanted,
            backgroundColor: 'rgba(54, 162, 235, 0.6)'
        }]
    },
    options: {
        responsive: true,
        title: {
            display: true,
            text: 'Avoka Qty Planted by Business Location in 2024'
        }
    }
});

// Expense Distribution (Pie Chart)
const ctx2 = document.getElementById('expensePieChart').getContext('2d');
new Chart(ctx2, {
    type: 'pie',
    data: {
        labels: districts,
        datasets: [{
            data: totalSpent,
            backgroundColor: ['rgba(255, 99, 132, 0.6)', 'rgba(54, 162, 235, 0.6)']
        }]
    },
    options: {
        responsive: true,
        title: {
            display: true,
            text: 'Farmer Last Year Expenses by District'
        }
    }
});

// Farmer Group Expenses (Bar Chart)
const ctx3 = document.getElementById('farmerGroupExpenseChart').getContext('2d');
new Chart(ctx3, {
    type: 'bar',
    data: {
        labels: farmerGroups,
        datasets: [{
            label: 'Total Expenses 2024 (M)',
            data: totalExpenses2024,
            backgroundColor: 'rgba(75, 192, 192, 0.6)'
        }]
    },
    options: {
        responsive: true,
        title: {
            display: true,
            text: 'Farmer Group Expenses in 2024'
        }
    }
});

// Seeds and Fertilizers (Bar Chart)
const ctx4 = document.getElementById('totalSeedsChart').getContext('2d');
new Chart(ctx4, {
    type: 'bar',
    data: {
        labels: districts,
        datasets: [{
            label: 'Total Spent on Seeds and Fertilizers',
            data: totalSpent,
            backgroundColor: 'rgba(153, 102, 255, 0.6)'
        }]
    },
    options: {
        responsive: true,
        title: {
            display: true,
            text: 'Total Amount Spent on Seeds and Fertilizers'
        }
    }
});

// Inkoko Qty Ordered (Bar Chart)
const ctx5 = document.getElementById('inkokoQtyChart').getContext('2d');
new Chart(ctx5, {
    type: 'bar',
    data: {
        labels: districts,
        datasets: [{
            label: 'Inkoko Qty Ordered in 2024',
            data: inkokoQtyOrdered,
            backgroundColor: 'rgba(255, 159, 64, 0.6)'
        }]
    },
    options: {
        responsive: true,
        title: {
            display: true,
            text: 'Inkoko Qty Ordered in 2024'
        }
    }
});
