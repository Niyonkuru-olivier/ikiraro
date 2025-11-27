// -------------------- SAMPLE DATA (CORRECTED) --------------------
const districts = ['Rwamagana', 'Kayonza'];

// Money values → numbers only (unit added later)
const totalSpent = [617388710, 632886700]; // RWF

// Avoka quantity planted → pure numbers
const avokaQtyPlanted = [2000, 1800, 1500, 1300]; // Kg

const farmerGroups = ['TUZAMURANE', 'TWITEZIMBERE', 'DUTERIMBERE', 'ICYEREKEZO', 'ABISHYIZEHAMWE'];

// Farmer expenses → numbers only
const totalExpenses2024 = [50000000, 45000000, 42000000, 39000000, 35000000]; // RWF (Millions)

// Inkoko (Chickens) ordered → pieces
const inkokoQtyOrdered = [29522, 17828]; // Pieces


// -------------------- CHART 1: Avoka Qty Planted --------------------
const ctx1 = document.getElementById('avokaQtyChart').getContext('2d');
new Chart(ctx1, {
    type: 'bar',
    data: {
        labels: ['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5'],
        datasets: [{
            label: 'Avoka Qty Planted in 2024 (Kg)',
            data: avokaQtyPlanted,
            backgroundColor: 'rgba(54, 162, 235, 0.6)'
        }]
    },
    options: {
        responsive: true,
        plugins: {
            tooltip: {
                callbacks: {
                    label: (ctx) => `${ctx.raw} Kg`
                }
            }
        }
    }
});


// -------------------- CHART 2: Expense Distribution Pie --------------------
const ctx2 = document.getElementById('expensePieChart').getContext('2d');
new Chart(ctx2, {
    type: 'pie',
    data: {
        labels: districts,
        datasets: [{
            data: totalSpent,
            backgroundColor: ['rgba(54, 99, 132, 0.6)', 'rgba(54, 162, 235, 0.6)']
        }]
    },
    options: {
        responsive: true,
        plugins: {
            tooltip: {
                callbacks: {
                    label: (ctx) => ctx.raw.toLocaleString() + " RWF"
                }
            }
        }
    }
});


// -------------------- CHART 3: Farmer Group Expenses --------------------
const ctx3 = document.getElementById('farmerGroupExpenseChart').getContext('2d');
new Chart(ctx3, {
    type: 'bar',
    data: {
        labels: farmerGroups,
        datasets: [{
            label: 'Total Expenses 2024 (RWF)',
            data: totalExpenses2024,
            backgroundColor: 'rgba(75, 192, 192, 0.6)'
        }]
    },
    options: {
        responsive: true,
        plugins: {
            tooltip: {
                callbacks: {
                    label: (ctx) => ctx.raw.toLocaleString() + " RWF"
                }
            }
        }
    }
});


// -------------------- CHART 4: Seeds & Fertilizers --------------------
const ctx4 = document.getElementById('totalSeedsChart').getContext('2d');
new Chart(ctx4, {
    type: 'bar',
    data: {
        labels: districts,
        datasets: [{
            label: 'Total Spent (RWF)',
            data: totalSpent,
            backgroundColor: 'rgba(153, 102, 255, 0.6)'
        }]
    },
    options: {
        responsive: true,
        plugins: {
            tooltip: {
                callbacks: {
                    label: (ctx) => ctx.raw.toLocaleString() + " RWF"
                }
            }
        }
    }
});


// -------------------- CHART 5: Inkoko Qty Ordered --------------------
const ctx5 = document.getElementById('inkokoQtyChart').getContext('2d');
new Chart(ctx5, {
    type: 'bar',
    data: {
        labels: districts,
        datasets: [{
            label: 'Inkoko Qty Ordered (Pieces)',
            data: inkokoQtyOrdered,
            backgroundColor: 'rgba(255, 159, 64, 0.6)'
        }]
    },
    options: {
        responsive: true,
        plugins: {
            tooltip: {
                callbacks: {
                    label: (ctx) => ctx.raw.toLocaleString() + " Pieces"
                }
            }
        }
    }
});
