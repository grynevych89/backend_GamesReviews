from django.urls import path
from products.services import steam_parser


def build_product_admin_urls(admin_view, views):
    """
    views: dict с bound-методами ProductAdmin:
      {
        'duplicate_product': self.duplicate_product,
        'toggle_is_active': self.toggle_is_active,
        'ajax_delete': self.ajax_delete,
        'upload_screenshot': self.upload_screenshot,
        'autosave_screenshots': self.autosave_screenshots,
        'get_categories': self.get_categories,
        'ajax_save_faq': self.ajax_save_faq,
        'ajax_delete_faq': self.ajax_delete_faq,
        'ajax_save_poll': self.ajax_save_poll,
        'ajax_delete_poll': self.ajax_delete_poll,
        'get_products': self.get_products,
        'best_products_autocomplete': self.best_products_autocomplete,
        'upload_image': self.upload_image,
      }
    """
    return [
        path("<int:product_id>/duplicate/", admin_view(views["duplicate_product"]), name="product-duplicate"),
        path("<int:pk>/toggle-active/", admin_view(views["toggle_is_active"]), name="products_product_toggle_active"),
        path("<int:pk>/delete-confirm/", admin_view(views["ajax_delete"]), name="product-delete-confirm"),
        path("upload-screenshot/", admin_view(views["upload_screenshot"]), name="product-upload-screenshot"),
        path("<int:pk>/autosave-screenshots/", admin_view(views["autosave_screenshots"]), name="products_product_autosave_screenshots"),
        path("get-categories/<str:product_type>/", admin_view(views["get_categories"]), name="products_product_get_categories"),
        path("faq/ajax-save/", admin_view(views["ajax_save_faq"]), name="faq-inline-save-new"),
        path("faq/<int:pk>/ajax-save/", admin_view(views["ajax_save_faq"]), name="faq-inline-save"),
        path("faq/<int:pk>/ajax-delete/", admin_view(views["ajax_delete_faq"]), name="faq-inline-delete"),
        path("<int:pk>/ajax-save-poll/", admin_view(views["ajax_save_poll"]), name="products_product_ajax_save_poll"),
        path("<int:pk>/ajax-delete-poll/<int:poll_id>/", admin_view(views["ajax_delete_poll"]), name="products_product_ajax_delete_poll"),
        path("get-products/<str:product_type>/", admin_view(views["get_products"]), name="products_product_get_products"),
        path("best-products-autocomplete/", admin_view(views["best_products_autocomplete"]), name="products_product_best_products_autocomplete"),
        path("upload-image/", admin_view(views["upload_image"]), name="products_product_upload_image"),

        # Steam parser (внешние view)
        path("parse-steam/", admin_view(steam_parser.parse_steam_view), name="products_product_parse_steam"),
        path("parse-steam/start/", admin_view(steam_parser.parse_steam_start), name="products_product_parse_steam_start"),
        path("parse-steam/status/<str:job_id>/", admin_view(steam_parser.parse_steam_status), name="products_product_parse_steam_status"),
        path("parse-steam/cancel/<str:job_id>/", admin_view(steam_parser.parse_steam_cancel), name="products_product_parse_steam_cancel"),
    ]
