document.addEventListener("DOMContentLoaded", function() {
    const original = document.querySelector('.form-row.field-rating');
    const top = document.querySelector('#top-rating-field');
    if (original && top) {
        const starWidget = original.querySelector('.star-rating');
        if (starWidget) {
            top.appendChild(starWidget);    // переносим оригинальный виджет
            original.style.display = 'none'; // скрываем нижнее поле
        }
    }
});
