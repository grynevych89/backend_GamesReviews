document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.screenshots-widget').forEach(widget => {
        const grid = widget.querySelector('.screenshots-grid');
        const fileInput = widget.querySelector('.screenshot-upload');
        const urlInput = widget.querySelector('.screenshot-url');
        const addUrlButton = widget.querySelector('.add-url-btn');
        const hiddenInput = widget.querySelector('.screenshots-json');

        let screenshots = [];
        try {
            screenshots = JSON.parse(hiddenInput.value || '[]');
        } catch {
            screenshots = [];
        }

        function renderGrid() {
            grid.innerHTML = '';
            screenshots.forEach((url, index) => {
                const item = document.createElement('div');
                item.className = 'screenshot-item';
                item.innerHTML = `
                    <img src="${url}" class="screenshot-thumb"/>
                    <div class="screenshot-actions">
                        <button type="button" class="move-left">←</button>
                        <button type="button" class="move-right">→</button>
                        <button type="button" class="delete">🗑</button>
                    </div>
                `;

                item.querySelector('.move-left').addEventListener('click', () => {
                    if (index > 0) {
                        [screenshots[index - 1], screenshots[index]] =
                            [screenshots[index], screenshots[index - 1]];
                        update();
                    }
                });

                item.querySelector('.move-right').addEventListener('click', () => {
                    if (index < screenshots.length - 1) {
                        [screenshots[index + 1], screenshots[index]] =
                            [screenshots[index], screenshots[index + 1]];
                        update();
                    }
                });

                item.querySelector('.delete').addEventListener('click', () => {
                    screenshots.splice(index, 1);
                    update();
                    showToast("🗑 Скриншот удалён");
                });

                grid.appendChild(item);
            });
            hiddenInput.value = JSON.stringify(screenshots);
        }

        function autosave() {
            const productId = window.location.pathname.split('/').filter(Boolean).slice(-2, -1)[0];
            const url = `/admin/products/product/${productId}/autosave-screenshots/`;

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: JSON.stringify({screenshots}),
            })
            .then(r => r.json())
            .then(data => {
                if (!data.success) {
                    console.error("Ошибка автосохранения:", data.error);
                    showToast("❌ Ошибка сохранения");
                } else {
                    showToast("✅ Скриншоты сохранены");
                }
            });
        }

        function showToast(message) {
            const container = document.querySelector('.screenshot-toast-container');
            if (!container) return;

            const toast = document.createElement('div');
            toast.className = 'screenshot-toast';
            toast.innerText = message;

            container.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }

        function update() {
            renderGrid();
            autosave();
        }

        function addUrlsFromInput() {
            const urls = urlInput.value
                .split(/[\n,]/) // разделяем по запятой или переносу строки
                .map(u => u.trim())
                .filter(u => u.length > 0);

            if (!urls.length) return;

            urls.forEach(url => screenshots.push(url));
            urlInput.value = '';
            update();
            showToast(`📸 Добавлено скриншотов: ${urls.length}`);
        }

        // ✅ Добавление по кнопке
        addUrlButton.addEventListener('click', addUrlsFromInput);

        // ✅ Добавление по Enter
        urlInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                addUrlsFromInput();
            }
        });

        // ✅ Множественная загрузка с компьютера
        fileInput.addEventListener('change', e => {
    const files = Array.from(e.target.files);
    if (!files.length) return;

    const totalFiles = files.length;
    let uploadedFiles = 0;

    // Загружаем все файлы параллельно
    Promise.all(files.map(file => {
        const formData = new FormData();
        formData.append('file', file);

        return fetch('/admin/products/product/upload-screenshot/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            body: formData
        })
        .then(r => r.json())
        .then(data => {
            if (data.url) {
                screenshots.push(data.url);
                uploadedFiles++;
            }
        });
    }))
    .then(() => {
        update();
        showToast(`📸 Добавлено скриншотов: ${uploadedFiles}/${totalFiles}`);
    });

    fileInput.value = ''; // Сбрасываем input
});


        renderGrid();
    });
});
