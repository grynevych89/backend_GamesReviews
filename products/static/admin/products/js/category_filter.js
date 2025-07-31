document.addEventListener('DOMContentLoaded', function () {
    const typeField = document.querySelector('#id_type');
    const categoryField = document.querySelector('#id_category');

    if (!typeField || !categoryField) return;

    typeField.addEventListener('change', function () {
        const type = this.value;
        if (!type) return;

        // ✅ Полностью сбрасываем выбранное значение
        categoryField.selectedIndex = 0;

        fetch(`/admin/products/product/get-categories/${type}/`)
            .then(response => response.json())
            .then(data => {
                // Полная очистка списка
                categoryField.innerHTML = '<option value="">---------</option>';

                // Заполнение новыми категориями
                data.forEach(cat => {
                    const option = document.createElement('option');
                    option.value = cat.id;
                    option.textContent = cat.display_name;
                    categoryField.appendChild(option);
                });

                // ✅ Сбрасываем выбор после подгрузки
                categoryField.value = '';
            })
            .catch(err => console.error(err));
    });
});
