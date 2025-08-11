TINYMCE_DEFAULT_CONFIG = {
    'height': 500,
    'menubar': 'file edit insert view format tools table help',
    'plugins': 'advlist autolink lists link image media code preview table fullscreen img100',
    'toolbar': (
        'undo redo | formatselect | bold italic underline | '
        'alignleft aligncenter alignright alignjustify | '
        'bullist numlist outdent indent | link image media uploadimage | '
        'code preview fullscreen'
    ),
    'automatic_uploads': True,
    'file_picker_types': 'file image media',
    'media_live_embeds': True,
    'content_css': 'default',
    'images_upload_url': '/admin/products/product/upload-image/',
    'image_dimensions': True,
    'image_default_width': '100%',
    'image_default_height': '100%',
    'content_style': (
        'img { max-width: 100%; height: auto; display: block; margin: 0 auto; } '
        'body, p, h1, h2, h3, h4, h5, h6 { max-width: 100%; }'
    ),
    'external_plugins': {
        'img100': '/static/admin/products/js/tinymce_img100.js',
    },
}