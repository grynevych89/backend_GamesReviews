document.getElementById('site-select').addEventListener('change', function () {
  const selectedValue = this.value;
  const url = new URL(window.location.href);

  url.searchParams.delete("site");
  url.searchParams.delete("product__site__id__exact");

  const isCommentPage = url.pathname.includes('/comment/');

  if (selectedValue) {
    if (isCommentPage) {
      url.searchParams.set("product__site__id__exact", selectedValue);
    } else {
      url.searchParams.set("site", selectedValue);
    }
  }

  window.location.href = url.toString();
});
