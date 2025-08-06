function toggleExtraFields() {
    const mode = document.getElementById("parse_mode").value;
    document.getElementById("manual_input").style.display = (mode === "manual") ? "block" : "none";
    document.getElementById("random_input").style.display = (mode === "random") ? "block" : "none";
}

// Инициализация при загрузке страницы
document.addEventListener("DOMContentLoaded", toggleExtraFields);
