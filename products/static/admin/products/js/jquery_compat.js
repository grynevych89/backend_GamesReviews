(function() {
  if (window.django && window.django.jQuery) {
    window.jQuery = window.jQuery || window.django.jQuery;
    window.$ = window.$ || window.django.jQuery;
  }
})();
