function validateRating(input) {
    const min = parseFloat(input.min);
    const max = parseFloat(input.max);
    const step = parseFloat(input.step);
    let value = parseFloat(input.value.replace(',', '.'));  // поддержка комы

    if (isNaN(value)) return;
    if (value < min) value = min;
    if (value > max) value = max;

    // Округление до ближайшего шага (0.5)
    value = Math.round(value / step) * step;

    // Устанавливаем значение с 1 знаком после запятой
    input.value = value.toFixed(1);
}
