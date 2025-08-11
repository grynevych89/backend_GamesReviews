PRODUCT_TYPE_CHOICES = [
    ('game', 'Game'),
    ('movie', 'Movie'),
    ('app', 'App'),
]

RATING_MIN = 4
RATING_MAX = 10

BUTTON_TEXT_BY_TYPE = {"game": "Get Game", "movie": "Watch Now", "app": "Get App"}

PRODUCT_DUPLICATE_EXCLUDE_FIELDS = [
    "id",
    "slug",
    "site",
    "created_at",
    "polls",
    "best_products",
    "screenshots",
    "category",
    "author",
    "publishers",
    "developers",
    "type",
]

IGNORED_MODELS = {
    "category",
}

