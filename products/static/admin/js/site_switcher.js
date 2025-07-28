document.addEventListener("DOMContentLoaded", function () {
  const siteSelect = document.getElementById("site-select");
  const currentUrl = new URL(window.location.href);

  const ENTITY_PARAM_MAP = {
    comment: "product__site__id__exact",
    product: "site",
    default: "site",
  };

  function detectParamName(path) {
    if (path.includes("/comment/")) return ENTITY_PARAM_MAP.comment;
    if (path.includes("/product/")) return ENTITY_PARAM_MAP.product;
    return ENTITY_PARAM_MAP.default;
  }

  const paramName = detectParamName(currentUrl.pathname);
  let currentSiteId = currentUrl.searchParams.get(paramName);

  // 🧠 Восстановим из sessionStorage если нет в URL
  if (!currentSiteId && sessionStorage.getItem("selected_site_id")) {
    currentSiteId = sessionStorage.getItem("selected_site_id");
  }

  // ⏺️ 1. Обработка переключения сайта
  if (siteSelect) {
    siteSelect.addEventListener("change", function () {
      const selectedValue = this.value;
      sessionStorage.setItem("selected_site_id", selectedValue);

      const url = new URL(window.location.href);
      Object.values(ENTITY_PARAM_MAP).forEach((param) => url.searchParams.delete(param));

      const param = detectParamName(url.pathname);
      if (selectedValue) {
        url.searchParams.set(param, selectedValue);
      }

      window.location.href = url.toString();
    });

    // 🪄 При загрузке — выбрать текущий сайт в шапке
    if (currentSiteId) {
      siteSelect.value = currentSiteId;
    }
  }

  // ⏺️ 2. Модификация всех ссылок
  if (currentSiteId) {
    document.querySelectorAll("a[href]:not([href^='#'])").forEach((link) => {
      const url = new URL(link.href, window.location.origin);
      const param = detectParamName(url.pathname);

      if (
        url.hostname === window.location.hostname &&
        url.pathname.startsWith("/admin/") &&
        !url.searchParams.has(param)
      ) {
        url.searchParams.set(param, currentSiteId);
        link.href = url.toString();
      }
    });
  }
});
