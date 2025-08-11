PRODUCT_FIELDSETS = [
    (
        None,
        {
            "fields": (
                (
                    "title",
                    "slug",
                    "type",
                    "category",
                    "required_age",
                    "publishers_str",
                    "developers_str",
                    "release_date",
                ),
                ("best_products", "length", "version", "director", "country", "actors_str"),
            ),
            "classes": ("fieldset-horizontal", "movie-info-fieldset", "block-separator"),
        },
    ),
    (
        None,
        {
            "fields": (
                ("min_os", "min_processor", "min_ram"),
                ("min_graphics", "min_storage", "min_additional"),
            ),
            "classes": ("fieldset-horizontal", "requirements-fieldset", "block-separator"),
        },
    ),
    (
        None,
        {
            "fields": (("official_website", "android_url", "app_store_url", "steam_url", "playstation_url"),),
            "classes": ("fieldset-horizontal", "block-separator"),
        },
    ),
    (None, {"fields": (("review_headline", "author"), "review_body"), "classes": ("block-separator",)}),
    (None, {"fields": (("pros", "cons"),), "classes": ("fieldset-horizontal", "block-separator")}),
    (
        None,
        {
            "fields": (("rating_1", "rating_2", "rating_3", "rating_4"),),
            "classes": ("fieldset-horizontal", "block-separator"),
        },
    ),
    (None, {"fields": (("seo_title", "seo_description"),), "classes": ("block-separator",)}),
    (
        None,
        {
            "fields": (("logo_preview", "logo_file", "logo_url"),),
            "classes": ("fieldset-horizontal", "block-separator"),
        },
    ),
    (None, {"fields": (("screenshots",),)}),
    (None, {"fields": ("rating",), "classes": ("hidden-fieldset", "block-separator")}),
]