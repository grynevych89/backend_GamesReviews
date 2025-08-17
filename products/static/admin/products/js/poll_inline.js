document.addEventListener("DOMContentLoaded", function () {
    const prefix = "polls";
    const productForm = document.querySelector("form#product_form") || document.querySelector("form");

    // ⚙️ Утилиты
    function getCookie(name) {
        let value = null;
        if (!document.cookie) return value;
        document.cookie.split(";").forEach(cookie => {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                value = decodeURIComponent(cookie.slice(name.length + 1));
            }
        });
        return value;
    }

    function showToast(message, icon = "✅", isError = false) {
        try {
            if (typeof window.showTopToast === "function") {
                window.showTopToast(`${icon} ${message}`);
                return;
            }
        } catch (_) {}
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
        setTimeout(() => (toast.style.opacity = 1), 50);
        setTimeout(() => {
            toast.style.opacity = 0;
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }

    function updateTotalForms(delta) {
        const input = document.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`);
        if (!input) return;
        const cur = parseInt(input.value || "0", 10);
        input.value = String(cur + delta);
    }

    function createAnswerRow() {
        const div = document.createElement("div");
        div.className = "poll-answer-row";
        div.innerHTML = `
            <input type="text" class="vTextField" placeholder="Вариант ответа"/>
            <button type="button" class="delete-answer-btn" title="Удалить">✖</button>
        `;
        const delBtn = div.querySelector(".delete-answer-btn");
        if (delBtn) {
            delBtn.onclick = ev => {
                ev.preventDefault();
                div.remove();
            };
        }
        return div;
    }

    function fillWithFourAnswers(container) {
        if (!container) return;
        container.innerHTML = "";
        for (let i = 0; i < 4; i++) {
            container.appendChild(createAnswerRow());
        }
    }

    // ⬆️ Загрузка фото
    async function uploadPollImage(pollId, row) {
        if (!pollId || !row) return;

        const fileInput = row.querySelector('input[type="file"][name$="-image"]');
        const file = fileInput && fileInput.files && fileInput.files[0];
        if (!file) return;

        const table = document.querySelector(`#${prefix}-group`);
        let endpoint = table && table.dataset && table.dataset.uploadTemplate;
        if (!endpoint) endpoint = `/admin/products/poll/0/upload-image/`;
        endpoint = endpoint.replace(/\/0\/upload-image\/?$/, `/${pollId}/upload-image/`);

        const formData = new FormData();
        formData.append("image", file);

        const resp = await fetch(endpoint, {
            method: "POST",
            body: formData,
            headers: {"X-CSRFToken": getCookie("csrftoken") || ""}
        });

        const data = await resp.json().catch(() => ({}));
        if (!data || !data.success) {
            throw new Error((data && data.error) || "Ошибка загрузки изображения");
        }

        const box = row.querySelector(".poll-image-preview, .poll-preview");
        if (box && data.url) {
            const oldImg = box.querySelector("img");
            if (oldImg && oldImg.src && oldImg.src.startsWith("blob:")) {
                try { URL.revokeObjectURL(oldImg.src); } catch (_) {}
            }
            box.innerHTML = '<img alt="" style="width:100%;height:100%;object-fit:contain;display:block;">';
            const img = box.querySelector("img");
            if (img) img.src = data.url;
        }

        try { fileInput.value = ""; } catch (_) {}
        if (fileInput && fileInput.files && fileInput.files.length) {
            const clone = fileInput.cloneNode(true);
            fileInput.parentNode.replaceChild(clone, fileInput);
        }
    }

    // 💾 Сохранение опроса
    async function ajaxSavePoll(row) {
        if (!row) return;

        const titleInput = row.querySelector('input[name$="-title"]');
        const title = (titleInput && typeof titleInput.value === "string") ? titleInput.value.trim() : "";

        const questionInput = row.querySelector('input[name$="-question"]');
        const question = (questionInput && typeof questionInput.value === "string") ? questionInput.value.trim() : "";
        const answersContainer = row.querySelector(".poll-answers-container");
        const answers = (answersContainer ? Array.from(answersContainer.querySelectorAll("input[type='text']")) : [])
            .map(i => (i && typeof i.value === "string") ? i.value.trim() : "")
            .filter(v => v);

        if (!question && answers.length === 0) return;
        if (question && answers.length === 0) throw new Error("Укажите хотя бы один вариант ответа");
        if (!question && answers.length > 0) throw new Error("Укажите вопрос для ваших ответов");

        const pollIdFromRow = row && row.dataset ? row.dataset.pollId : "";
        let pollId = pollIdFromRow || "";

        const parts = window.location.pathname.split("/").filter(Boolean);
        const idx = parts.indexOf("product");
        const productId = idx >= 0 && /^\d+$/.test(parts[idx + 1] || "") ? parts[idx + 1] : null;
        if (!productId) throw new Error("Не удалось определить product_id");

        const url = `/admin/products/product/${productId}/ajax-save-poll/` + (pollId ? `?poll_id=${pollId}` : "");

        const resp = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken") || ""
            },
            body: JSON.stringify({title, question, answers})
        });

        const data = await resp.json().catch(() => ({}));
        if (!data || !data.success) {
            throw new Error((data && data.error) || "Ошибка сохранения");
        }

        pollId = data.poll_id;
        if (row && row.dataset) row.dataset.pollId = pollId;

        let idInput = row.querySelector('input[name$="-id"]');
        if (!idInput) {
            const q = questionInput;
            if (q && q.name) {
                const idName = q.name.replace(/-question$/, "-id");
                idInput = row.querySelector(`input[name="${CSS.escape(idName)}"]`);
                if (!idInput) {
                    idInput = document.createElement("input");
                    idInput.type = "hidden";
                    idInput.name = idName;
                    row.appendChild(idInput);
                }
            }
        }
        if (idInput) idInput.value = String(pollId);

        await uploadPollImage(pollId, row);
    }

    function markEmptyForDeletion() {
        const rows = document.querySelectorAll(`#${prefix}-group .form-row:not(.empty-form)`);
        rows.forEach(row => {
            const q = row.querySelector(`input[name$="-question"]`);
            const del = row.querySelector(`input[name$="-DELETE"]`);
            if (q && typeof q.value === "string" && !q.value.trim() && del) {
                del.checked = true;
            }
        });
    }

    // 📨 Общий сабмит
    async function handleSubmit(e) {
        if (!productForm) return;
        e.preventDefault();

        const rows = Array.from(document.querySelectorAll(`#${prefix}-group .form-row:not(.empty-form)`));

        try {
            for (const row of rows) {
                await ajaxSavePoll(row);
            }
        } catch (err) {
            showToast(err && err.message ? err.message : "Ошибка", "⚠️", true);
            return;
        }

        markEmptyForDeletion();
        productForm.setAttribute("enctype", "multipart/form-data");
        productForm.removeEventListener("submit", handleSubmit);
        productForm.submit();
    }

    function interceptSubmit() {
        if (!productForm) return;
        productForm.setAttribute("enctype", "multipart/form-data");
        productForm.addEventListener("submit", handleSubmit);
    }

    // 🗑️ Удаление опроса
    async function ajaxDeletePoll(pollId) {
        if (!pollId) throw new Error("Нет ID опроса");
        if (!confirm("Вы уверены?")) throw new Error("Отменено");

        const parts = window.location.pathname.split("/").filter(Boolean);
        const idx = parts.indexOf("product");
        const productId = idx >= 0 && /^\d+$/.test(parts[idx + 1] || "") ? parts[idx + 1] : null;
        if (!productId) throw new Error("Не удалось определить product_id");

        const url = `/admin/products/product/${productId}/ajax-delete-poll/${pollId}/`;
        const resp = await fetch(url, {
            method: "POST",
            headers: {"X-CSRFToken": getCookie("csrftoken") || ""}
        });
        const data = await resp.json().catch(() => ({}));
        if (!data || !data.success) throw new Error((data && data.error) || "Ошибка удаления");
    }

    async function reloadPollInline() {
        const resp = await fetch(window.location.href, {
            headers: {"X-Requested-With": "XMLHttpRequest"}
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

    // 🖼 Превью локального файла
    document.addEventListener("change", function (e) {
        const input = e.target && e.target.closest && e.target.closest('input[type="file"]');
        if (!input) return;
        const row = input.closest && input.closest(".form-row, tr, .inline-related, .dynamic-polls");
        if (!row) return;
        const box = row.querySelector(".poll-image-preview, .poll-preview");
        const file = (input.files && input.files[0]) ? input.files[0] : null;
        if (!box || !file) return;

        const url = URL.createObjectURL(file);
        box.innerHTML = '<img alt="" style="width:100%;height:100%;object-fit:contain;display:block;">';
        const img = box.querySelector("img");
        if (img) img.src = url;
    });

    // 🛠 Инициализация
    function wireRow(row) {
        if (!row) return;

        const del = row.querySelector(".poll-delete-button");
        if (del) {
            del.onclick = async e => {
                e.preventDefault();
                const pollId =
                    (row.dataset && row.dataset.pollId) ||
                    (del.dataset && del.dataset.pollId) ||
                    (del.dataset && del.dataset.id) ||
                    null;
                if (!pollId) {
                    showToast("Сохраните опрос, чтобы его можно было удалить.", "ℹ️");
                    return;
                }
                try {
                    await ajaxDeletePoll(pollId);
                    showToast("Удалено", "🗑️");
                    await reloadPollInline();
                } catch (err) {
                    showToast(err && err.message ? err.message : "Ошибка удаления", "⚠️", true);
                }
            };
        }

        const addAns = row.querySelector(".add-option-btn");
        if (addAns) {
            addAns.onclick = e => {
                e.preventDefault();
                const container = row.querySelector(".poll-answers-container");
                if (container) container.appendChild(createAnswerRow());
            };
        }

        const delBtns = row.querySelectorAll(".delete-answer-btn");
        delBtns.forEach(btn => {
            btn.onclick = e => {
                e.preventDefault();
                const item = btn.closest(".poll-answer-row");
                if (item && item.parentNode) item.parentNode.removeChild(item);
            };
        });
    }

    function initPollInline() {
        document.querySelectorAll(`#${prefix}-group .form-row`).forEach(wireRow);

        const addBtn = document.querySelector(`#add_${prefix}`);
        if (addBtn) {
            addBtn.onclick = e => {
                e.preventDefault();
                const empty = document.getElementById(`${prefix}-empty`);
                const totalInput = document.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`);
                if (!empty || !totalInput) return;

                const count = parseInt(totalInput.value || "0", 10);
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
                wireRow(newRow);
            };
        }
    }

    initPollInline();
    interceptSubmit();
});
