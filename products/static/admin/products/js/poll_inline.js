document.addEventListener("DOMContentLoaded", function () {
    const productForm = document.querySelector('form#product_form');

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function showToast(message, icon = '✅', isError = false) {
        const toast = document.createElement('div');
        toast.className = 'admin-toast';
        toast.innerHTML = `${icon} ${message}`;
        Object.assign(toast.style, {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            padding: '8px 14px',
            color: 'white',
            fontWeight: 'bold',
            borderRadius: '4px',
            zIndex: 9999,
            backgroundColor: isError ? '#d33' : '#000',
            opacity: '0',
            transition: 'opacity 0.3s'
        });
        document.body.appendChild(toast);
        setTimeout(() => (toast.style.opacity = '1'), 50);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }

    function getProductId() {
        const parts = window.location.pathname.split('/').filter(Boolean);
        return parts[parts.length - 2];
    }

    // 🔹 Перезагрузка PollInline
    async function reloadPollInline() {
        const response = await fetch(window.location.href, {headers: {'X-Requested-With': 'XMLHttpRequest'}});
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newTable = doc.querySelector('#polls-group');
        const currentTable = document.querySelector('#polls-group');
        if (newTable && currentTable) {
            currentTable.innerHTML = newTable.innerHTML;
            initPollInline();
        }
    }

    // 🔹 Ajax сохранение
    async function ajaxSavePoll(questionInput, answersContainer, saveBtn, row) {
        const question = questionInput.value.trim();
        const answers = Array.from(answersContainer.querySelectorAll('input[type="text"]'))
            .map(i => i.value.trim())
            .filter(Boolean);

        if (!question || answers.length === 0) return;

        const pollId = saveBtn.dataset.pollId || null;
        const productId = getProductId();
        const url = `/admin/products/product/${productId}/ajax-save-poll/` + (pollId ? `?poll_id=${pollId}` : '');

        const response = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken')},
            body: JSON.stringify({question, answers})
        });

        const data = await response.json();
        if (data.success) {
            showToast('Опрос сохранён!', '✅');
            await reloadPollInline(); // обновляем список
        } else {
            showToast(data.error || 'Ошибка сохранения', '⚠️', true);
        }
    }

    // 🔹 Ajax удаление
    async function ajaxDeletePoll(pollId) {
        if (!confirm("Вы уверены, что хотите удалить этот опрос?")) return;

        const productId = getProductId();
        const url = `/admin/products/product/${productId}/ajax-delete-poll/${pollId}/`;

        const response = await fetch(url, {method: 'POST', headers: {'X-CSRFToken': getCookie('csrftoken')}});
        const data = await response.json();
        if (data.success) {
            showToast('Опрос удалён', '🗑️');
            await reloadPollInline(); // обновляем список
        } else {
            showToast(data.error || 'Ошибка удаления', '⚠️', true);
        }
    }

    function initAnswerRow(answerRow) {
        const deleteBtn = answerRow.querySelector('.delete-answer-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.preventDefault();
                answerRow.remove();
            });
        }
    }

    function initPollRow(row) {
        const answersContainer = row.querySelector('.poll-answers-container');
        const addAnswerBtn = row.querySelector('.add-option-btn');
        const deleteBtn = row.querySelector('.poll-delete-button');
        const saveBtn = row.querySelector('.poll-save-button');
        const questionInput = row.querySelector('input[name$="question"]');

        row.querySelectorAll('.poll-answer-row').forEach(initAnswerRow);

        if (addAnswerBtn) {
            addAnswerBtn.addEventListener('click', (e) => {
                e.preventDefault();
                const div = document.createElement('div');
                div.className = 'poll-answer-row';
                div.innerHTML = `
                    <input type="text" placeholder="Вариант ответа" class="vTextField"/>
                    <button type="button" class="delete-answer-btn">✖</button>
                `;
                answersContainer.appendChild(div);
                initAnswerRow(div);
            });
        }

        if (saveBtn && questionInput) {
            saveBtn.addEventListener('click', (e) => {
                e.preventDefault();
                ajaxSavePoll(questionInput, answersContainer, saveBtn, row);
            });
        }

        if (deleteBtn && row.dataset.pollId) {
            deleteBtn.addEventListener('click', (e) => {
                e.preventDefault();
                ajaxDeletePoll(row.dataset.pollId);
            });
        }
    }

    function initPollInline() {
        document.querySelectorAll('#polls-group .form-row').forEach((row) => {
            if (!row.classList.contains('empty-form')) {
                initPollRow(row);
            }
        });

        const addPollBtn = document.querySelector('#add_polls');
        if (addPollBtn) {
            addPollBtn.addEventListener('click', (e) => {
                e.preventDefault();
                const emptyForm = document.querySelector('#polls-empty');
                if (!emptyForm) {
                    showToast("Не найдена empty-form для PollInline", '⚠️', true);
                    return;
                }
                const formIndex = document.querySelectorAll('#polls-group .dynamic-polls').length;
                const newRow = emptyForm.cloneNode(true);
                newRow.classList.remove('empty-form');
                newRow.classList.add('dynamic-polls');
                newRow.innerHTML = newRow.innerHTML.replace(/__prefix__/g, formIndex);
                newRow.style.display = '';
                emptyForm.parentNode.insertBefore(newRow, emptyForm);
                initPollRow(newRow);
            });
        }
    }

    // 🔹 Общая кнопка Save
if (productForm) {
    productForm.addEventListener('submit', async function (event) {
        // Сохраняем все строки через Ajax
        const rows = document.querySelectorAll('#polls-group .form-row:not(.empty-form)');
        for (const row of rows) {
            const questionInput = row.querySelector('input[name$="question"]');
            const answersContainer = row.querySelector('.poll-answers-container');
            const saveBtn = row.querySelector('.poll-save-button');

            if (questionInput && questionInput.value.trim()) {
                await ajaxSavePoll(questionInput, answersContainer, saveBtn, row);
            }
        }

        // Полностью удаляем все строки и скрытую форму
        const pollGroup = document.querySelector('#polls-group');
        if (pollGroup) pollGroup.remove();

        // Обнуляем management form ДО отправки
        document.querySelectorAll('input[name$="-TOTAL_FORMS"], input[name$="-INITIAL_FORMS"]').forEach(input => {
            input.value = 0;
        });

        // Удаляем все inputs Poll, чтобы Django их не видел в POST
        document.querySelectorAll('input[name^="polls-"]').forEach(input => input.remove());
    });
}





    initPollInline();
});
