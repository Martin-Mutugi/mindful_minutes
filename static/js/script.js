  // 📊 Mood Chart - Enhanced for Dark Mode
  const chartEl = document.getElementById('moodChart');
  if (chartEl) {
    try {
      const dates = JSON.parse(chartEl.dataset.dates || '[]'); // Use .dataset
      const scores = JSON.parse(chartEl.dataset.scores || '[]');

      // Check if there's data to display
      if (dates.length === 0) {
        console.log("No chart data available.");
        return; // Exit gracefully if no data
      }

      // Function to get CSS variable for light/dark mode
      const getCssVar = (varName) => {
        return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
      };

      // Define colors using CSS variables from your style.css
      const textColor = getCssVar('--text-color'); // e.g., #333 in light, #f0f0f0 in dark
      const gridColor = getCssVar('--border-color'); // e.g., #ddd in light, #444 in dark
      const chartBgColor = getCssVar('--card-bg'); // Card background for tooltips
      const primaryColor = getCssVar('--primary-color'); // Your main green color

      new Chart(chartEl, {
        type: 'line',
        data: {
          labels: dates,
          datasets: [{
            label: 'Mood Score',
            data: scores,
            borderColor: primaryColor, // Use your theme's primary color
            backgroundColor: 'rgba(76, 175, 80, 0.1)', // Keep this subtle opacity
            pointBackgroundColor: primaryColor,
            pointRadius: 5,
            pointHoverRadius: 7,
            fill: true,
            tension: 0.3 // Smooth line
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false, // Crucial for the chart-container to control size
          animation: {
            duration: 1500, // Slightly longer for a smoother feel
            easing: 'easeOutQuart'
          },
          plugins: {
            legend: {
              position: 'top',
              labels: {
                color: textColor, // Dynamically adapts to light/dark mode
                font: { size: 14, weight: '600' }
              }
            },
            tooltip: {
              backgroundColor: chartBgColor,
              titleColor: textColor,
              bodyColor: textColor,
              callbacks: {
                label: (ctx) => `Score: ${ctx.parsed.y.toFixed(3)}` // More precise tooltip
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              suggestedMax: 1, // Slightly better than 'max' for empty data
              ticks: {
                stepSize: 0.2,
                color: textColor // Adapt ticks to mode
              },
              grid: {
                color: gridColor // Adapt grid to mode
              },
              title: {
                display: true,
                text: 'Sentiment Score',
                color: textColor, // Adapt title to mode
                font: { size: 14, weight: '600' }
              }
            },
            x: {
              ticks: {
                color: textColor, // Adapt ticks to mode
                maxRotation: 45, // Prevent label overlap on many dates
              },
              grid: {
                color: gridColor // Adapt grid to mode
              },
              title: {
                display: true,
                text: 'Date',
                color: textColor, // Adapt title to mode
                font: { size: 14, weight: '600' }
              }
            }
          }
        }
      });

    } catch (err) {
      console.error("Chart rendering failed:", err);
      // Optionally, you could display a user-friendly error message in the chart container here
      chartEl.style.display = 'none';
    }
  }