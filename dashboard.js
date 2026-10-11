/**
 * InternSpark - Dashboard Charts & Metrics
 */

document.addEventListener('DOMContentLoaded', () => {
  // Check if student application chart exists
  const studentChartCanvas = document.getElementById('studentAppChart');
  if (studentChartCanvas && typeof Chart !== 'undefined') {
    const interested = parseInt(studentChartCanvas.dataset.interested || 0);
    const applied = parseInt(studentChartCanvas.dataset.applied || 0);
    const interview = parseInt(studentChartCanvas.dataset.interview || 0);
    const offered = parseInt(studentChartCanvas.dataset.offered || 0);
    const rejected = parseInt(studentChartCanvas.dataset.rejected || 0);

    new Chart(studentChartCanvas, {
      type: 'doughnut',
      data: {
        labels: ['Interested', 'Applied', 'Interview', 'Offered', 'Rejected'],
        datasets: [{
          data: [interested, applied, interview, offered, rejected],
          backgroundColor: ['#94a3b8', '#3b82f6', '#f59e0b', '#10b981', '#ef4444'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { boxWidth: 12, font: { family: 'Plus Jakarta Sans', size: 12 } }
          }
        },
        cutout: '72%'
      }
    });
  }

  // Admin Charts
  const adminStatusCanvas = document.getElementById('adminStatusChart');
  if (adminStatusCanvas && typeof Chart !== 'undefined') {
    const rawData = JSON.parse(adminStatusCanvas.dataset.json || '{}');
    const labels = Object.keys(rawData);
    const dataValues = Object.values(rawData);

    new Chart(adminStatusCanvas, {
      type: 'bar',
      data: {
        labels: labels.length ? labels : ['No Data'],
        datasets: [{
          label: 'Applications Count',
          data: dataValues.length ? dataValues : [0],
          backgroundColor: '#6366f1',
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1 } }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }
});
