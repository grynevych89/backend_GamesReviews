document.addEventListener("DOMContentLoaded", function () {
    initFAQButtons();

    // --- Инициализация кнопок ---
    function initFAQButtons() {
        document.querySelectorAll(".faq-save-button").forEach(attachSaveHandler);
        document.querySelectorAll(".faq-delete-button").forEach(attachDeleteHandler);
        document.querySelectorAll(".delete-button").forEach(attachDeleteHandler); // скриншоты / продукты в списке
    }

    // --- AJAX сохранение FAQ ---
    function attachSaveHandler(button) {
        button.addEventListener("click", function () {
            const row = this.closest("tr");
            const questionInput = row.querySelector('input[name$="question"]');
            const answerInput = row.querySelector('input[name$="answer"]');
            const idInput = row.querySelector('input[name$="id"]');
            const faqId = idInput && idInput.value ? idInput.value : null;

            const question = questionInput ? questionInput.value.trim() : "";
            const answer = answerInput ? answerInput.value.trim() : "";

            if (!question || !answer) {
                showFAQToast("❌ Заполните оба поля перед сохранением");
                return;
            }

            const productId = getProductIdFromUrl();
            const url = faqId
                ? `/admin/products/product/faq/${faqId}/ajax-save/`
                : `/admin/products/product/faq/ajax-save/?product_id=${productId}`;

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ question: question, answer: answer })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showFAQToast(faqId ? "✅ FAQ обновлён" : "✅ FAQ добавлен");

                        if (data.id && !faqId && idInput) {
                            idInput.value = data.id;
                        }

                        // 🔹 Обновляем список FAQ без перезагрузки
                        reloadFAQInline();
                    } else {
                        showFAQToast("❌ Ошибка: " + (data.error || "Неизвестно"));
                    }
                });
        });
    }

    // --- AJAX удаление FAQ / скриншотов / продукта в списке ---
    function attachDeleteHandler(button) {
        button.addEventListener("click", function (e) {
            e.preventDefault();

            const url = this.dataset.url;
            if (!url) return;

            const row = this.closest("tr");
            const isFAQ = this.classList.contains("faq-delete-button");

            if (!row) return;
            if (!confirm("Вы уверены, что хотите удалить?")) return;

            fetch(url, {
                method: "POST",
                headers: { "X-CSRFToken": getCSRFToken() },
            })
                .then(res => res.json())
                .then(data => {
                    if (!data.success) {
                        const msg = "❌ Ошибка: " + (data.error || "Неизвестно");
                        return isFAQ ? showFAQToast(msg) : showTopToast(msg);
                    }

                    // Успешно
                    if (isFAQ) {
                        showFAQToast("🗑️ FAQ удалён");
                        reloadFAQInline();
                        return;
                    }

                    // Определяем контекст: скриншот или продукт в общем списке
                    const inChangeList = !!document.querySelector("form#changelist-form");
                    const isProductRow = inChangeList && !!row.querySelector('input.action-select');

                    // Сносим строку
                    row.remove();

                    if (isProductRow) {
                        // 📦 Удаление продукта в общем списке
                        showTopToast("🗑️ Продукт удалён");
                        // Пытаемся обновить стандартный счётчик Django Admin
                        if (window.Actions && typeof window.Actions.updateCounter === "function") {
                            try { window.Actions.updateCounter(); } catch (e) {}
                        }
                        // Фолбэк: прямое обновление текста
                        updateActionCounterFallback();
                    } else {
                        // 🖼️ Удаление скриншота (или любой другой не-чейнлист кейс)
                        showTopToast("🗑️ Скриншот удалён");
                        // На всякий случай обновим счётчик, если есть чекбоксы в зоне
                        updateActionCounterFallback();
                    }
                });
        });
    }

    // --- Перезагрузка FAQ инлайна через fetch ---
    function reloadFAQInline() {
        const container = document.querySelector('#faqs-group');
        if (!container) return;

        fetch(window.location.href, { headers: { "X-Requested-With": "XMLHttpRequest" } })
            .then(res => res.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, "text/html");
                const newInline = doc.querySelector('#faqs-group');
                if (newInline) {
                    container.innerHTML = newInline.innerHTML;
                    initFAQButtons(); // заново подключаем кнопки
                }
            });
    }

    // --- Фолбэк-обновление счётчика выбранных объектов в changelist ---
    function updateActionCounterFallback() {
        const form = document.querySelector('form#changelist-form');
        if (!form) return;
        const checkboxes = form.querySelectorAll('input.action-select');
        const selected = form.querySelectorAll('input.action-select:checked').length;
        const counter = document.querySelector('.action-counter');
        if (counter) {
            counter.textContent = `${selected} of ${checkboxes.length} selected`;
        }
    }

    // --- Тост справа внизу для FAQ ---
    function showFAQToast(text) {
        const toast = document.createElement('div');
        toast.textContent = text;
        toast.style.position = 'fixed';
        toast.style.bottom = '20px';
        toast.style.right = '20px';
        toast.style.background = 'rgba(0,0,0,0.85)';
        toast.style.color = '#fff';
        toast.style.padding = '10px 15px';
        toast.style.marginTop = '10px';
        toast.style.borderRadius = '5px';
        toast.style.zIndex = 10000;
        toast.style.fontSize = '14px';
        toast.style.display = 'flex';
        toast.style.alignItems = 'center';
        toast.style.gap = '6px';
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }

    // --- Тост сверху (для скриншотов/продуктов) ---
    function showTopToast(text) {
        const toast = document.createElement('div');
        toast.textContent = text;
        toast.style.position = 'fixed';
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.background = 'rgba(0,0,0,0.85)';
        toast.style.color = '#fff';
        toast.style.padding = '10px 15px';
        toast.style.marginTop = '10px';
        toast.style.borderRadius = '5px';
        toast.style.zIndex = 10000;
        toast.style.fontSize = '14px';
        toast.style.display = 'flex';
        toast.style.alignItems = 'center';
        toast.style.gap = '6px';
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }

    // --- CSRF токен ---
    function getCSRFToken() {
        const name = "csrftoken";
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        return '';
    }

    // --- Получаем product_id из URL ---
    function getProductIdFromUrl() {
        const match = window.location.pathname.match(/product\/(\d+)\/change/);
        return match ? match[1] : null;
    }
});
