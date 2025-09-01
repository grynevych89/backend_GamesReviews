from .category import Author

class AuthorProxy(Author):
    class Meta:
        proxy = True
        app_label = "references"
        verbose_name = "Author"
        verbose_name_plural = "Authors"
