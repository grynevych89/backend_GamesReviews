document.addEventListener("DOMContentLoaded", function () {
    const typeSelect = document.querySelector("#id_type");
    if (!typeSelect) return;

    const labelMap = {
        game: ["Story Rating", "Directing Rating", "Soundtrack Rating", "Special Effects Rating"],
        movie: ["Plot Rating", "Acting Rating", "Soundtrack Rating", "Visual Effects Rating"],
        app: ["UX Rating", "Performance Rating", "Stability Rating", "Features Rating"],
    };

    const fields = [
        document.querySelector("label[for='id_rating_1']"),
        document.querySelector("label[for='id_rating_2']"),
        document.querySelector("label[for='id_rating_3']"),
        document.querySelector("label[for='id_rating_4']"),
    ];

    function updateLabels() {
        const typeValue = typeSelect.value;
        if (labelMap[typeValue]) {
            fields.forEach((label, index) => {
                if (label) label.textContent = labelMap[typeValue][index];
            });
        }
    }

    updateLabels();
    typeSelect.addEventListener("change", updateLabels);
});
