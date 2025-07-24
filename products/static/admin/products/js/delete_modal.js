document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".delete-button").forEach(function (button) {
        button.addEventListener("click", function (e) {
            e.preventDefault();
            const url = this.dataset.url;
            const self = this;

            if (confirm("Вы уверены, что хотите удалить?")) {
                fetch(url, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCSRFToken(),
                    },
                })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            const row = self.closest("tr");
                            if (row) row.remove();

                            // ✅ Обновить счётчик
                            const checkboxes = document.querySelectorAll('input.action-select');
                            const selected = document.querySelectorAll('input.action-select:checked').length;
                            const counter = document.querySelector('.action-counter');

                            if (counter) {
                                counter.textContent = `${selected} of ${checkboxes.length} selected`;
                            }
                        } else {
                            alert("Ошибка: " + (data.error || "Неизвестно"));
                        }
                    });
            }
        });
    });

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
});

