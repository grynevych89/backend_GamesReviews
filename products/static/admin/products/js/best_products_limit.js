document.addEventListener('DOMContentLoaded', function () {
    const typeSelect = document.getElementById('id_type');
    const bestSelect = document.getElementById('id_best_products');
    if (!bestSelect) return;

    const $select = django.jQuery(bestSelect); // ✅ используем встроенный jQuery

    // Добавляем предупреждение
    let warning = document.createElement('div');
    warning.style.color = 'red';
    warning.style.marginTop = '5px';
    warning.style.display = 'none';
    warning.textContent = 'Можно выбрать максимум 4 продукта.';
    bestSelect.parentNode.appendChild(warning);

    // Инициализация Select2
    $select.select2({
        width: '500px',
        maximumSelectionLength: 4,
        closeOnSelect: true,
        ajax: {
            url: '/admin/products/product/best-products-autocomplete/',
            delay: 250,
            data: function (params) {
                return {
                    term: params.term,
                    type: typeSelect ? typeSelect.value : null,
                    selected: $select.val() || []
                };
            },
            processResults: function (data) {
                return {
                    results: data.results
                };
            }
        }
    });

    function checkLimit() {
        const selectedCount = $select.select2('data').length;
        warning.style.display = selectedCount >= 4 ? 'block' : 'none';
    }

    $select.on('select2:select select2:unselect', checkLimit);

    if (typeSelect) {
        typeSelect.addEventListener('change', function () {
            $select.val(null).trigger('change.select2');
            checkLimit();
        });
    }
});
