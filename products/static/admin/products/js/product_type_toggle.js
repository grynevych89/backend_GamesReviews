document.addEventListener('DOMContentLoaded', function () {
    const typeField = document.querySelector('#id_type');

    const formRow = document.querySelector('.form-row.field-length.field-version');
    const lengthBox = document.querySelector('.fieldBox.field-length');
    const versionBox = document.querySelector('.fieldBox.field-version');
    const lengthLabel = document.querySelector('label[for="id_length"]');
    const versionLabel = document.querySelector('label[for="id_version"]');

    const requirementsFieldset = document.querySelector('fieldset.requirements-fieldset');

    // 🔹 Поля Movie
    const directorBox = document.querySelector('.fieldBox.field-director');
    const countryBox = document.querySelector('.fieldBox.field-country');
    const actorsBox = document.querySelector('.fieldBox.field-actors_str'); // виртуальное поле actors_str

    function toggleFields() {
        const type = typeField.value;

        // --- Length / Version ---
        const showLength = type === 'movie';
        const showVersion = type === 'app';

        if (lengthBox) lengthBox.style.display = showLength ? '' : 'none';
        if (lengthLabel) lengthLabel.style.display = showLength ? '' : 'none';

        if (versionBox) versionBox.style.display = showVersion ? '' : 'none';
        if (versionLabel) versionLabel.style.display = showVersion ? '' : 'none';

        if (formRow) {
            formRow.style.display = (showLength || showVersion) ? '' : 'none';
            formRow.style.borderBottom = (showLength || showVersion) ? '' : 'none';
        }

        // --- Минимальные требования ---
        if (requirementsFieldset) {
            requirementsFieldset.style.display = (type === 'game' || type === 'app') ? '' : 'none';
        }

        // --- Поля только для Movie ---
        const showMovieFields = type === 'movie';
        if (directorBox) directorBox.style.display = showMovieFields ? '' : 'none';
        if (countryBox) countryBox.style.display = showMovieFields ? '' : 'none';
        if (actorsBox) actorsBox.style.display = showMovieFields ? '' : 'none';
    }

    if (typeField) {
        toggleFields(); // при загрузке
        typeField.addEventListener('change', toggleFields); // при смене
    }
});
