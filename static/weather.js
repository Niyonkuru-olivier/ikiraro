(function () {
  const canvas = document.getElementById('cropYieldChart');
  if (!canvas || typeof Chart === 'undefined') return;
  new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: {
      labels: ['2018', '2019', '2020', '2021', '2022'],
      datasets: [{
        label: 'Crop Yield (tons)',
        data: [1.5, 2.0, 2.5, 3.0, 3.5],
        borderColor: 'rgba(76, 175, 80, 1)',
        backgroundColor: 'rgba(76, 175, 80, 0.2)',
        borderWidth: 2,
        fill: true
      }]
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true } }
    }
  });
})();

(function () {
  const widgets = document.querySelectorAll('[data-weather-widget]');
  if (!widgets.length) return;

  const ENDPOINT = '/api/weather';
  const CACHE_WINDOW = 60 * 1000;
  let cache = null;
  let cacheTimestamp = 0;
  let inflight = null;

  const getValue = (object, path) => {
    if (!object || !path) return null;
    return path.split('.').reduce((acc, key) => (acc && acc[key] !== undefined ? acc[key] : null), object);
  };

  const formatValue = (value, format) => {
    if (value === null || value === undefined || value === '') return '—';
    const numeric = Number(value);
    switch (format) {
      case 'temperature':
        return Number.isFinite(numeric) ? `${Math.round(numeric)}°C` : `${value}°C`;
      case 'percentage':
        return Number.isFinite(numeric) ? `${Math.round(numeric)}%` : `${value}%`;
      case 'precipitation':
        return Number.isFinite(numeric) ? `${numeric.toFixed(1)} mm` : `${value} mm`;
      case 'speed':
        return Number.isFinite(numeric) ? `${numeric.toFixed(1)} km/h` : `${value} km/h`;
      default:
        if (Number.isFinite(numeric)) {
          return numeric.toFixed(1).replace(/\.0$/, '');
        }
        return value;
    }
  };

  const iconUrl = (icon) => {
    if (!icon) return '';
    if (icon.startsWith('http')) return icon;
    if (icon.startsWith('//')) return `https:${icon}`;
    return icon;
  };

  const buildForecastHtml = (forecast = [], extended = false) => {
    if (!forecast.length) {
      return '<p>No forecast data available.</p>';
    }
    const limit = extended ? 5 : 3;
    return forecast.slice(0, limit).map((day) => {
      const icon = iconUrl(day.icon);
      const rain = day.daily_chance_of_rain ? `<span class="weather-rain-chip">${day.daily_chance_of_rain}% rain</span>` : '';
      return `
        <article>
          <p class="weather-forecast__date">${day.date || ''}</p>
          <img src="${icon || ''}" alt="${day.condition || ''}">
          <div>
            <p class="weather-forecast__temps">${day.max_temp_c ?? '—'}° / ${day.min_temp_c ?? '—'}°</p>
            <small>${day.condition || ''}</small>
            ${rain}
          </div>
        </article>
      `;
    }).join('');
  };

  const buildAlertsHtml = (alerts = []) => {
    if (!alerts.length) {
      return '<p class="weather-alerts__empty">No active weather alerts across Rwanda.</p>';
    }
    return alerts.map((alert) => `
      <article>
        <h5>${alert.headline || alert.category || 'Advisory'}</h5>
        <p>${alert.note || 'Stay alert for local advisories.'}</p>
        <small>Severity: ${alert.severity || 'Info'} · Areas: ${alert.areas || 'Nationwide'}</small>
      </article>
    `).join('');
  };

  const buildDistrictTickerHtml = (districts = [], errorMessage, updatedAt) => {
    if (!districts.length && errorMessage) {
      return `<p class="weather-districts__empty">${errorMessage}</p>`;
    }
    if (!districts.length) {
      return '<p class="weather-districts__empty">Loading district-level conditions across Rwanda...</p>';
    }
    const items = districts.map((district) => {
      const temp = Number.isFinite(district.temp_c) ? `${Math.round(district.temp_c)}°C` : '—';
      const condition = district.condition ? `<small>${district.condition}</small>` : '';
      return `
        <span class="weather-districts__item">
          <strong>${district.name || '—'}</strong>
          <span>${temp}</span>
          ${condition}
        </span>
      `;
    }).join('');
    const ghostItems = districts.map((district) => {
      const temp = Number.isFinite(district.temp_c) ? `${Math.round(district.temp_c)}°C` : '—';
      const condition = district.condition ? `<small>${district.condition}</small>` : '';
      return `
        <span class="weather-districts__item weather-districts__item--ghost">
          <strong>${district.name || '—'}</strong>
          <span>${temp}</span>
          ${condition}
        </span>
      `;
    }).join('');
    const notice = errorMessage ? `<em>${errorMessage}</em>` : '';
    return `
      <div class="weather-districts__meta">
        <span>Rwanda climate pulse</span>
        <small>Updated ${updatedAt || '—'}</small>
        ${notice}
      </div>
      <div class="weather-districts__ticker" data-weather-districts-track>
        ${items}${ghostItems}
      </div>
    `;
  };

  const fetchWeather = async (force = false) => {
    if (!force && cache && (Date.now() - cacheTimestamp) < CACHE_WINDOW) {
      return cache;
    }
    if (!force && inflight) {
      return inflight;
    }
    const url = force ? `${ENDPOINT}?refresh=1` : ENDPOINT;
    inflight = fetch(url)
      .then((res) => res.json())
      .then((data) => {
        cache = data;
        cacheTimestamp = Date.now();
        return data;
      })
      .catch(() => ({ error: 'Unable to load weather data.' }))
      .finally(() => {
        inflight = null;
      });
    return inflight;
  };

  const updateWidget = (widget, data) => {
    const body = widget.querySelector('[data-weather-body]');
    const errorBox = widget.querySelector('[data-weather-error]');
    if (!data || data.error) {
      if (errorBox) {
        errorBox.hidden = false;
        const messageEl = errorBox.querySelector('p');
        if (messageEl) {
          messageEl.textContent = (data && data.error) || 'Weather data is currently unavailable.';
        }
      }
      if (body) body.hidden = true;
      return;
    }

    if (errorBox) errorBox.hidden = true;
    if (body) body.hidden = false;

    widget.querySelectorAll('[data-weather-key]').forEach((node) => {
      const key = node.dataset.weatherKey;
      const format = node.dataset.weatherFormat;
      const value = getValue(data, key);
      node.textContent = format ? formatValue(value, format) : (value ?? '—');
    });

    const iconEl = widget.querySelector('[data-weather-icon]');
    if (iconEl) {
      const icon = iconUrl(getValue(data, 'current.icon'));
      if (icon) iconEl.src = icon;
    }

    const forecastContainer = widget.querySelector('[data-weather-forecast]');
    if (forecastContainer) {
      const extended = (widget.dataset.variant || 'compact') === 'extended';
      forecastContainer.innerHTML = buildForecastHtml(data.forecast || [], extended);
    }

    const alertsContainer = widget.querySelector('[data-weather-alerts]');
    if (alertsContainer) {
      alertsContainer.innerHTML = buildAlertsHtml(data.alerts || []);
    }

    const districtTicker = widget.querySelector('[data-weather-districts]');
    if (districtTicker) {
      districtTicker.innerHTML = buildDistrictTickerHtml(
        data.districts || [],
        data.districts_error,
        data.districts_updated_at
      );
    }
  };

  const refreshWidget = async (widget, force = false) => {
    const data = await fetchWeather(force);
    updateWidget(widget, data);
  };

  widgets.forEach((widget) => {
    const initialScript = widget.querySelector('[data-weather-initial]');
    if (initialScript) {
      try {
        updateWidget(widget, JSON.parse(initialScript.textContent));
      } catch (error) {
        refreshWidget(widget);
      }
    } else {
      refreshWidget(widget);
    }

    const retryBtn = widget.querySelector('[data-weather-retry]');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => refreshWidget(widget, true));
    }

    const refreshSeconds = Number(widget.dataset.refreshSeconds || 300);
    if (refreshSeconds > 0) {
      setInterval(() => refreshWidget(widget), refreshSeconds * 1000);
    }
  });
})();
