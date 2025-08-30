document.addEventListener('DOMContentLoaded', function () {
  // 🌙 Dark Mode Toggle
  const darkToggle = document.getElementById('darkToggle');
  if (darkToggle) {
    darkToggle.addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
    });
  }

  // ⏳ Journal Form Loading Spinner
  const journalForm = document.querySelector('.journal-form');
  const loadingSpinner = document.getElementById('loadingSpinner');
  if (journalForm && loadingSpinner) {
    journalForm.addEventListener('submit', () => {
      loadingSpinner.style.display = 'block';
    });
  }

  // 📊 Mood Chart
  const ctx = document.getElementById('moodChart');
  if (ctx) {
    const dates = JSON.parse(ctx.getAttribute('data-dates'));
    const scores = JSON.parse(ctx.getAttribute('data-scores'));

    new Chart(ctx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: [{
          label: 'Mood Score',
          data: scores,
          borderColor: '#4CAF50',
          backgroundColor: 'rgba(76, 175, 80, 0.1)',
          pointBackgroundColor: '#388E3C',
          pointRadius: 4,
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: true,
            labels: {
              color: '#333',
              font: {
                size: 14,
                weight: 'bold'
              }
            }
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                return `Score: ${context.parsed.y.toFixed(2)}`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 1,
            ticks: {
              stepSize: 0.1
            },
            title: {
              display: true,
              text: 'Mood Score',
              color: '#333',
              font: {
                size: 14
              }
            }
          },
          x: {
            title: {
              display: true,
              text: 'Date',
              color: '#333',
              font: {
                size: 14
              }
            }
          }
        }
      }
    });
  }

  // ⏱️ Meditation Timer
  const timerBtn = document.getElementById('timerBtn');
  const timerDisplay = document.getElementById('timer');

  if (timerBtn && timerDisplay) {
    timerBtn.addEventListener('click', function () {
      let timeLeft = 120;
      timerBtn.disabled = true;
      timerBtn.textContent = "Meditation in progress...";

      const timerInterval = setInterval(() => {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        timerDisplay.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

        if (timeLeft <= 0) {
          clearInterval(timerInterval);
          timerDisplay.textContent = "🧘 Time's up!";
          timerBtn.disabled = false;
          timerBtn.textContent = "Start 2-Minute Timer";
        }

        timeLeft--;
      }, 1000);
    });
  }
});
