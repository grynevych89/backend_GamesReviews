document.addEventListener('DOMContentLoaded', function () {
    const typeField = document.querySelector('#id_type');

    const formRow = document.querySelector('.form-row.field-length.field-version');
    const lengthBox = document.querySelector('.fieldBox.field-length');
    const versionBox = document.querySelector('.fieldBox.field-version');
    const lengthLabel = document.querySelector('label[for="id_length"]');
    const versionLabel = document.querySelector('label[for="id_version"]');

    function toggleFields() {
        const type = typeField.value;

        const showLength = type === 'movie';
        const showVersion = type === 'app';

        // Поля и лейблы
        if (lengthBox) lengthBox.style.display = showLength ? '' : 'none';
        if (lengthLabel) lengthLabel.style.display = showLength ? '' : 'none';

        if (versionBox) versionBox.style.display = showVersion ? '' : 'none';
        if (versionLabel) versionLabel.style.display = showVersion ? '' : 'none';

        // Прячем всю строку, если оба поля скрыты
        if (formRow) {
            if (showLength || showVersion) {
                formRow.style.display = '';
                formRow.style.borderBottom = '';
            } else {
                formRow.style.display = 'none';
                // убираем бордер, если он есть
                formRow.style.borderBottom = 'none';
            }
        }
    }

    if (typeField) {
        toggleFields(); // при загрузке
        typeField.addEventListener('change', toggleFields); // при смене
    }
});
