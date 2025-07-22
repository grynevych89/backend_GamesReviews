document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("is-active-toggle");
  const notice = document.getElementById("is-active-notice");

  if (!toggle) return;

  toggle.addEventListener("change", function () {
    const url = this.dataset.url;
    const isActive = this.checked;

    fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({ is_active: isActive }),
    })
      .then((response) => {
        if (!response.ok) throw new Error("Server error");
        return response.json();
      })
      .then((data) => {
        showNotice("Статус оновлено ✓");
      })
      .catch((error) => {
        console.error("Toggle error:", error);
        showNotice("Помилка!", true);
      });
  });

  function showNotice(message, isError = false) {
    if (!notice) return;
    notice.textContent = message;
    notice.classList.remove("error");
    if (isError) notice.classList.add("error");
    notice.style.display = "inline-block";

    setTimeout(() => {
      notice.style.display = "none";
    }, 2500);
  }

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + "=")) {
          cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});
