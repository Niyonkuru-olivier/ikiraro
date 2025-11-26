(function () {
  const canvas = document.getElementById('cropYieldChart');
  if (canvas && typeof Chart !== 'undefined') {
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
  }
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

  const buildDistrictCardsHtml = (districts = [], errorMessage, strings = {}) => {
    if (!districts.length && errorMessage) {
      return `<p class="weather-marquee__empty">${errorMessage}</p>`;
    }
    if (!districts.length) {
      return `<p class="weather-marquee__empty">${strings.districtEmpty || 'Loading weather data...'}</p>`;
    }

    const buildCard = (district, isClone = false) => {
      const temp = Number.isFinite(district.temp_c) ? `${Math.round(district.temp_c)}°C` : '—';
      const condition = district.condition ? `<span class="weather-marquee__condition">${district.condition}</span>` : '';
      const cloneClass = isClone ? ' weather-marquee__card--clone' : '';
      return `
        <div class="weather-marquee__card${cloneClass}">
          <span class="weather-marquee__district">${district.name || '—'}</span>
          <span class="weather-marquee__temp">${temp}</span>
          ${condition}
        </div>
      `;
    };

    const cards = districts.map(d => buildCard(d, false)).join('');
    const clones = districts.map(d => buildCard(d, true)).join('');

    return `
      <div class="weather-marquee__track" data-weather-districts-track>
        ${cards}${clones}
      </div>
    `;
  };

  const updateWidget = (widget, data, strings) => {
    const body = widget.querySelector('[data-weather-body]');
    const errorBox = widget.querySelector('[data-weather-error]');

    if (!data || data.error) {
      if (errorBox) {
        errorBox.hidden = false;
        const messageEl = errorBox.querySelector('p');
        if (messageEl) {
          messageEl.textContent = (data && data.error) || strings.errorGeneric || 'Weather unavailable';
        }
      }
      if (body) body.hidden = true;
      return;
    }

    if (errorBox) errorBox.hidden = true;
    if (body) body.hidden = false;

    const districtContainer = widget.querySelector('[data-weather-districts]');
    if (districtContainer) {
      districtContainer.innerHTML = buildDistrictCardsHtml(
        data.districts || [],
        data.districts_error,
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
      errorGeneric: getString(widget, 'i18nErrorGeneric', 'Unable to load weather data.'),
      districtEmpty: getString(widget, 'i18nDistrictEmpty', 'Loading weather data...'),
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
