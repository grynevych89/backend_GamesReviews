document.addEventListener("DOMContentLoaded", function () {
    const prefix = "polls";  // префикс inline formset
    const productForm = document.querySelector("form#product_form");

    // ────────────────────────────────
    // ⚙️ Утилиты
    // ────────────────────────────────
    function getCookie(name) {
        let value = null;
        document.cookie.split(";").forEach(cookie => {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                value = decodeURIComponent(cookie.slice(name.length + 1));
            }
        });
        return value;
    }

    function showToast(message, icon = "✅", isError = false) {
        const toast = document.createElement("div");
        toast.className = "admin-toast";
        toast.innerHTML = `${icon} ${message}`;
        Object.assign(toast.style, {
            position: "fixed", bottom: "20px", right: "20px",
            padding: "8px 14px", color: "white", fontWeight: "bold",
            borderRadius: "4px", zIndex: 9999,
            backgroundColor: isError ? "#d33" : "#000",
            opacity: 0, transition: "opacity 0.3s"
        });
        document.body.appendChild(toast);
        setTimeout(() => toast.style.opacity = 1, 50);
        setTimeout(() => {
            toast.style.opacity = 0;
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }

    function updateTotalForms(delta) {
        const input = document.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`);
        input.value = parseInt(input.value, 10) + delta;
    }

    function createAnswerRow() {
        const div = document.createElement("div");
        div.className = "poll-answer-row";
        div.innerHTML = `
            <input type="text" class="vTextField" placeholder="Вариант ответа"/>
            <button type="button" class="delete-answer-btn">✖</button>
        `;
        div.querySelector(".delete-answer-btn").onclick = ev => {
            ev.preventDefault();
            div.remove();
        };
        return div;
    }

    function fillWithFourAnswers(container) {
        if (!container) return;
        container.innerHTML = "";
        for (let i = 0; i < 4; i++) {
            container.appendChild(createAnswerRow());
        }
    }

    // ────────────────────────────────
    // 💾 Сохранение и удаление через AJAX
    // ────────────────────────────────
    async function ajaxSavePoll(row) {
        const questionInput = row.querySelector('input[name$="-question"]');
        const answers = Array.from(
            row.querySelectorAll(".poll-answers-container input[type='text']")
        ).map(i => i.value.trim()).filter(v => v);

        if (!questionInput.value.trim() && answers.length === 0) return;
        if (questionInput.value.trim() && answers.length === 0) {
            throw new Error("Укажите хотя бы один вариант ответа");
        }
        if (!questionInput.value.trim() && answers.length > 0) {
            throw new Error("Укажите вопрос для ваших ответов");
        }

        const saveBtn = row.querySelector(".poll-save-button");
        const pollId = saveBtn.dataset.pollId || "";
        const productId = window.location.pathname.split("/").slice(-3, -1)[0];
        const url =
            `/admin/products/product/${productId}/ajax-save-poll/` +
            (pollId ? `?poll_id=${pollId}` : "");

        const resp = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({
                question: questionInput.value.trim(),
                answers
            })
        });
        const data = await resp.json();
        if (!data.success) throw new Error(data.error || "Ошибка сохранения");

        saveBtn.dataset.pollId = data.poll_id;
        row.dataset.pollId = data.poll_id;
    }

    async function ajaxDeletePoll(pollId) {
        if (!confirm("Вы уверены?")) throw new Error("Отменено");
        const productId = window.location.pathname.split("/").slice(-3, -1)[0];
        const url = `/admin/products/product/${productId}/ajax-delete-poll/${pollId}/`;
        const resp = await fetch(url, {
            method: "POST",
            headers: { "X-CSRFToken": getCookie("csrftoken") }
        });
        const data = await resp.json();
        if (!data.success) throw new Error(data.error || "Ошибка удаления");
    }

    function markEmptyForDeletion() {
        document
            .querySelectorAll(`#${prefix}-group .form-row:not(.empty-form)`)
            .forEach(row => {
                const q = row.querySelector(`input[name$="-question"]`);
                const del = row.querySelector(`input[name$="-DELETE"]`);
                if (q && !q.value.trim() && del) {
                    del.checked = true;
                }
            });
    }

    async function handleSubmit(e) {
        e.preventDefault();

        const rows = Array.from(
            document.querySelectorAll(`#${prefix}-group .form-row:not(.empty-form)`)
        );

        try {
            for (const row of rows) {
                await ajaxSavePoll(row);
                showToast("Сохранено", "✅");
            }
        } catch (err) {
            showToast(err.message, "⚠️", true);
            return;
        }

        markEmptyForDeletion();
        productForm.removeEventListener("submit", handleSubmit);
        productForm.submit();
    }

    function interceptSubmit() {
        if (!productForm) return;
        productForm.addEventListener("submit", handleSubmit);
    }

    async function reloadPollInline() {
        const resp = await fetch(window.location.href, {
            headers: { "X-Requested-With": "XMLHttpRequest" }
        });
        const html = await resp.text();
        const doc = new DOMParser().parseFromString(html, "text/html");
        const newTbl = doc.querySelector(`#${prefix}-group`);
        const curTbl = document.querySelector(`#${prefix}-group`);
        if (newTbl && curTbl) {
            curTbl.replaceWith(newTbl);
            initPollInline();
        }
    }

    // ────────────────────────────────
    // 🛠 Инициализация
    // ────────────────────────────────
    function initPollInline() {
        // Подключаем кнопки к существующим строкам
        document.querySelectorAll(`#${prefix}-group .form-row`).forEach(row => {
            const del = row.querySelector(".poll-delete-button");
            if (del && row.dataset.pollId) {
                del.onclick = async e => {
                    e.preventDefault();
                    try {
                        await ajaxDeletePoll(row.dataset.pollId);
                        showToast("Удалено", "🗑️");
                        await reloadPollInline();
                    } catch (err) {
                        showToast(err.message, "⚠️", true);
                    }
                };
            }

            const save = row.querySelector(".poll-save-button");
            if (save) {
                save.onclick = async e => {
                    e.preventDefault();
                    try {
                        await ajaxSavePoll(row);
                        showToast("Сохранено", "✅");
                        await reloadPollInline();
                    } catch (err) {
                        showToast(err.message, "⚠️", true);
                    }
                };
            }

            row.querySelectorAll(".delete-answer-btn").forEach(btn => {
                btn.onclick = e => {
                    e.preventDefault();
                    btn.closest(".poll-answer-row").remove();
                };
            });

            const addAns = row.querySelector(".add-option-btn");
            if (addAns) {
                addAns.onclick = e => {
                    e.preventDefault();
                    const container = row.querySelector(".poll-answers-container");
                    container.appendChild(createAnswerRow());
                };
            }
        });

        // 🔹 Кнопка "Добавить опрос"
        const addBtn = document.querySelector(`#add_${prefix}`);
        if (addBtn) {
            addBtn.onclick = e => {
                e.preventDefault();
                const empty = document.getElementById(`${prefix}-empty`);
                const totalInput = document.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`);
                const count = parseInt(totalInput.value, 10);

                const newRow = empty.cloneNode(true);
                newRow.id = "";
                newRow.style.display = "";
                newRow.classList.remove("empty-form");
                newRow.classList.add("dynamic-polls");
                newRow.innerHTML = newRow.innerHTML.replace(/__prefix__/g, count);

                const answersContainer = newRow.querySelector(".poll-answers-container");
                fillWithFourAnswers(answersContainer);

                empty.parentNode.insertBefore(newRow, empty);
                updateTotalForms(+1);
                initPollInline();
            };
        }
    }

    initPollInline();
    interceptSubmit();
});
