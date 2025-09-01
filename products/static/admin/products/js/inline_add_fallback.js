(function(dj) {
  if (!dj) return;
  dj(function() {
    dj(document).on("click", 'tr.add-row a[id^="add_"]', function(e) {
      // Если inlines.js уже навесил preventDefault, выходим
      if (e.isDefaultPrevented && e.isDefaultPrevented()) return;

      const $link = dj(this);
      const $group = $link.closest('.inline-group[data-inline-formset]');
      if ($group.length === 0) return;

      e.preventDefault();

      const prefix = this.id.replace(/^add_/, "");
      const $tbody = $link.closest("tbody");
      const $total = dj(`#id_${prefix}-TOTAL_FORMS`);
      let index = parseInt(($total.val() || "0"), 10);

      const $tmpl = dj(`#${prefix}-empty`).clone(true);
      $tmpl
        .removeAttr("id")
        .removeClass("empty-form")
        .show();

      // Заменяем __prefix__ → индекс
      const html = $tmpl.html().replace(/__prefix__/g, String(index));
      $tmpl.html(html);

      // Вставляем перед add-row
      const $addRow = $tbody.find("tr.add-row");
      if ($addRow.length) {
        $addRow.before($tmpl);
      } else {
        $tbody.append($tmpl);
      }

      $total.val(index + 1);
    });
  });
})(window.django && window.django.jQuery);
