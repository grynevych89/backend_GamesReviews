(function () {
  const POLL_MS = 500;

  let pollTimer = null;
  let isRunning = false;
  let currentJobId = null;

  const qs = (sel) => document.querySelector(sel);

  function getCsrf() {
    const el = qs('#parseSteamForm [name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  function toggleExtraFields() {
    const mode = qs("#parse_mode").value;
    qs("#manual_input").style.display = (mode === "manual") ? "block" : "none";
    qs("#random_input").style.display = (mode === "random") ? "block" : "none";
  }

  function setBar(pct) {
    const bar = qs("#bar");
    const pctEl = qs("#pct");
    const clamped = Math.max(0, Math.min(100, Math.round(pct)));
    bar.style.width = clamped + "%";
    pctEl.textContent = clamped + "%";
  }

  function renderLog(list) {
    const log = qs("#log");
    log.innerHTML = '';
    (list || []).forEach(line => {
      const li = document.createElement('li');
      li.textContent = line;
      log.appendChild(li);
    });
    log.scrollTop = log.scrollHeight;
  }

  function enableForm(enabled) {
    qs("#parse_mode").disabled = !enabled;
    const rc = qs("#random_count");
    if (rc) rc.disabled = !enabled;
    const si = qs("#steam_ids");
    if (si) si.disabled = !enabled;
  }

  function setStartButton(state) {
    const btn = qs("#startBtn");
    if (state === "idle") {
      btn.disabled = false;
      btn.textContent = "Начать парсинг";
    } else if (state === "running") {
      btn.disabled = true;
      btn.textContent = "Запущено…";
    }
  }

  function setCancelButtonMode(mode) {
    const btn = qs("#cancelBtn");
    const listUrl = qs("#parseSteamRoot").dataset.listUrl;
    if (mode === "back") {
      btn.textContent = "Назад";
      btn.setAttribute("href", listUrl);
      btn.onclick = null; // обычный переход по ссылке
    } else if (mode === "cancel") {
      btn.textContent = "Отмена";
      btn.removeAttribute("href"); // не уходим со страницы
      btn.onclick = async (e) => {
        e.preventDefault();
        if (!currentJobId) return;
        // запрос отмены
        const cancelTpl = qs("#parseSteamRoot").dataset.cancelUrlTemplate;
        const url = cancelTpl.replace('JOB_ID', currentJobId);
        try {
          await fetch(url, { method: 'POST', headers: { 'X-CSRFToken': getCsrf() } });
          // дальше воркер сам увидит флаг и завершит; просто ждём d.done в poll
        } catch (_) {}
      };
    }
  }

  function toIdleUI() {
    isRunning = false;
    setStartButton("idle");
    enableForm(true);
    setCancelButtonMode("back"); // снова «Назад»
    currentJobId = null;
  }

  function toRunningUI() {
    isRunning = true;
    setStartButton("running");
    enableForm(false);
    setCancelButtonMode("cancel"); // в процессе — «Отмена»
    const progress = qs("#progress");
    progress.style.display = 'block';
    setBar(0);
    qs("#meta").textContent = "—";
    renderLog([]);
  }

  function clearPoll() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function poll(jobId, urls) {
    currentJobId = jobId;
    const statusUrl = urls.statusTpl.replace('JOB_ID', jobId);

    clearPoll();

    pollTimer = setInterval(async () => {
      let res;
      try {
        res = await fetch(statusUrl, { headers: { "X-Requested-With": "XMLHttpRequest" }});
      } catch {
        return;
      }
      if (!res.ok) return;

      const d = await res.json();

      const total = d.total || 1;
      const processed = d.processed || 0;
      const added = d.added || 0;
      const errors = d.errors || 0;

      const pct = total ? (processed / total) * 100 : 0;
      setBar(pct);
      qs("#meta").textContent = `Обработано: ${processed} / ${total} · добавлено: ${added} · ошибок: ${errors}`;
      renderLog(d.items || []);

      if (d.done) {
        clearPoll();
        setBar(100);
        toIdleUI(); // по завершении — «Начать парсинг» и кнопка «Назад»
      }
    }, POLL_MS);
  }

  async function startParsing() {
    if (isRunning) return;

    const root = qs("#parseSteamRoot");
    const form = qs("#parseSteamForm");
    const startUrl = root.dataset.startUrl;
    const statusTpl = root.dataset.statusUrlTemplate;

    const fd = new FormData(form);

    toRunningUI();

    let res;
    try {
      res = await fetch(startUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrf() },
        body: fd
      });
    } catch {
      alert('Не удалось запустить парсинг');
      toIdleUI();
      return;
    }

    if (!res.ok) {
      alert('Ошибка запуска парсинга');
      toIdleUI();
      return;
    }

    const data = await res.json();
    poll(data.job_id, { statusTpl });
  }

  document.addEventListener("DOMContentLoaded", function () {
    toggleExtraFields();
    qs("#parse_mode").addEventListener("change", toggleExtraFields);
    qs("#startBtn").addEventListener("click", startParsing);
  });
})();
