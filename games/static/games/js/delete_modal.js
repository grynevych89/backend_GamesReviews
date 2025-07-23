document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".delete-button").forEach(button => {
        button.addEventListener("click", function (e) {
            e.preventDefault();
            const url = this.dataset.url;

            if (confirm("Вы уверены, что хотите удалить?")) {
                fetch(url, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCSRFToken(),
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert("Ошибка при удалении: " + (data.error || "Неизвестно"));
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
