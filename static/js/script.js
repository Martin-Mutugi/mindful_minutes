document.addEventListener('DOMContentLoaded', () => {
  // 🌙 Dark Mode Toggle
  const darkToggle = document.getElementById('darkToggle');
  if (darkToggle) {
    darkToggle.addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
      darkToggle.classList.toggle('active');
    });
  }

  // ⏳ Global Spinner Hide on Load
  const loadingSpinner = document.getElementById('loadingSpinner');
  window.addEventListener('load', () => {
    if (loadingSpinner) loadingSpinner.style.display = 'none';
  });

  // 🧠 Journal Form Spinner
  const journalForm = document.querySelector('.journal-form');
  if (journalForm && loadingSpinner) {
    journalForm.addEventListener('submit', () => {
      loadingSpinner.style.display = 'block';
      setTimeout(() => {
        loadingSpinner.style.display = 'none';
      }, 5000); // fallback in case response fails
    });
  }

  // 📊 Mood Chart
  const chartEl = document.getElementById('moodChart');
  if (chartEl) {
    try {
      const dates = JSON.parse(chartEl.getAttribute('data-dates'));
      const scores = JSON.parse(chartEl.getAttribute('data-scores'));

      new Chart(chartEl, {
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
          animation: {
            duration: 800,
            easing: 'easeOutQuart'
          },
          plugins: {
            legend: {
              labels: {
                color: '#333',
                font: { size: 14, weight: 'bold' }
              }
            },
            tooltip: {
              callbacks: {
                label: ctx => `Score: ${ctx.parsed.y.toFixed(2)}`
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 1,
              ticks: { stepSize: 0.1 },
              title: {
                display: true,
                text: 'Mood Score',
                color: '#333',
                font: { size: 14 }
              }
            },
            x: {
              title: {
                display: true,
                text: 'Date',
                color: '#333',
                font: { size: 14 }
              }
            }
          }
        }
      });
    } catch (err) {
      console.error("Chart rendering failed:", err);
      chartEl.style.display = 'none';
    }
  }

  // ⏱️ Meditation Timer
  const timerBtn = document.getElementById('timerBtn');
  const timerDisplay = document.getElementById('timer');

  if (timerBtn && timerDisplay) {
    timerBtn.addEventListener('click', () => {
      let timeLeft = 120;
      timerBtn.disabled = true;
      timerBtn.textContent = "Meditation in progress...";

      const interval = setInterval(() => {
        const min = Math.floor(timeLeft / 60);
        const sec = timeLeft % 60;
        timerDisplay.textContent = `${min}:${sec < 10 ? '0' : ''}${sec}`;

        if (timeLeft <= 0) {
          clearInterval(interval);
          timerDisplay.textContent = "🧘 Time's up!";
          timerBtn.disabled = false;
          timerBtn.textContent = "Start 2-Minute Timer";
        }

        timeLeft--;
      }, 1000);
    });
  }
});
