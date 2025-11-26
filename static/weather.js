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

  const getString = (widget, key, fallback) => widget.dataset[key] || fallback;

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

  const buildForecastHtml = (forecast = [], extended = false, strings = {}) => {
    if (!forecast.length) {
      return `<p>${strings.forecastEmpty || 'No forecast data available.'}</p>`;
    }
    const limit = extended ? 5 : 3;
    return forecast.slice(0, limit).map((day) => {
      const icon = iconUrl(day.icon);
      const rainSuffix = strings.rainLabel || '% rain';
      const rain = day.daily_chance_of_rain ? `<span class="weather-rain-chip">${day.daily_chance_of_rain}${rainSuffix}</span>` : '';
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

  const buildAlertsHtml = (alerts = [], strings = {}) => {
    if (!alerts.length) {
      return `<p class="weather-alerts__empty">${strings.alertsEmpty || 'No active weather alerts across Rwanda.'}</p>`;
    }
    return alerts.map((alert) => `
      <article>
        <h5>${alert.headline || alert.category || strings.alertsHeadline || 'Advisory'}</h5>
        <p>${alert.note || strings.alertsNote || 'Stay alert for local advisories.'}</p>
        <small>${strings.severityLabel || 'Severity'}: ${alert.severity || 'Info'} · ${strings.areasLabel || 'Areas'}: ${alert.areas || 'Nationwide'}</small>
      </article>
    `).join('');
  };

  const buildDistrictTickerHtml = (districts = [], errorMessage, updatedAt, strings = {}) => {
    if (!districts.length && errorMessage) {
      return `<p class="weather-districts__empty">${errorMessage}</p>`;
    }
    if (!districts.length) {
      return `<p class="weather-districts__empty">${strings.districtEmpty || 'Loading district-level conditions across Rwanda...'}</p>`;
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
        <span>${strings.districtTitle || 'Rwanda climate pulse'}</span>
        <small>${strings.updatedLabel || 'Updated'} ${updatedAt || '—'}</small>
        ${notice}
      </div>
      <div class="weather-districts__ticker" data-weather-districts-track>
        ${items}${ghostItems}
      </div>
    `;
  };

  const fetchWeather = async (force = false, strings) => {
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
      .catch(() => ({ error: (strings && strings.errorGeneric) || 'Unable to load weather data.' }))
      .finally(() => {
        inflight = null;
      });
    return inflight;
  };

  const updateWidget = (widget, data, strings) => {
    const body = widget.querySelector('[data-weather-body]');
    const errorBox = widget.querySelector('[data-weather-error]');
    if (!data || data.error) {
      if (errorBox) {
        errorBox.hidden = false;
        const messageEl = errorBox.querySelector('p');
        if (messageEl) {
          messageEl.textContent = (data && data.error) || strings.errorGeneric || 'Weather data is currently unavailable.';
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
      forecastContainer.innerHTML = buildForecastHtml(data.forecast || [], extended, strings);
    }

    const alertsContainer = widget.querySelector('[data-weather-alerts]');
    if (alertsContainer) {
      alertsContainer.innerHTML = buildAlertsHtml(data.alerts || [], strings);
    }

    const districtTicker = widget.querySelector('[data-weather-districts]');
    if (districtTicker) {
      districtTicker.innerHTML = buildDistrictTickerHtml(
        data.districts || [],
        data.districts_error,
        data.districts_updated_at,
        strings
      );
    }
  };

  const refreshWidget = async (widget, strings, force = false) => {
    const data = await fetchWeather(force, strings);
    updateWidget(widget, data, strings);
  };

  widgets.forEach((widget) => {
    const strings = {
      forecastEmpty: getString(widget, 'i18nForecastEmpty', 'No forecast data available.'),
      alertsEmpty: getString(widget, 'i18nAlertsEmpty', 'No active weather alerts across Rwanda.'),
      alertsNote: getString(widget, 'i18nAlertsNote', 'Stay alert for local advisories.'),
      alertsHeadline: getString(widget, 'i18nAlertsHeadline', 'Advisory'),
      errorGeneric: getString(widget, 'i18nErrorGeneric', 'Unable to load weather data.'),
      districtEmpty: getString(widget, 'i18nDistrictEmpty', 'Loading district-level conditions across Rwanda...'),
      districtTitle: getString(widget, 'i18nDistrictTitle', 'Rwanda climate pulse'),
      updatedLabel: getString(widget, 'i18nUpdatedLabel', 'Updated'),
      rainLabel: getString(widget, 'i18nRainLabel', '% rain'),
      severityLabel: getString(widget, 'i18nSeverityLabel', 'Severity'),
      areasLabel: getString(widget, 'i18nAreasLabel', 'Areas'),
    };

    const initialScript = widget.querySelector('[data-weather-initial]');
    if (initialScript) {
      try {
        updateWidget(widget, JSON.parse(initialScript.textContent), strings);
      } catch (error) {
        refreshWidget(widget, strings);
      }
    } else {
      refreshWidget(widget, strings);
    }

    const retryBtn = widget.querySelector('[data-weather-retry]');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => refreshWidget(widget, strings, true));
    }

    const refreshSeconds = Number(widget.dataset.refreshSeconds || 300);
    if (refreshSeconds > 0) {
      setInterval(() => refreshWidget(widget, strings), refreshSeconds * 1000);
    }
  });
})();
