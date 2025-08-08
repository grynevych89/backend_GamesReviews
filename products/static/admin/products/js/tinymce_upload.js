function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        let cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

tinymce.init({
    selector: 'textarea.tinymce-field',
    plugins: 'advlist autolink lists link image media code preview table fullscreen',
    toolbar: 'undo redo | formatselect | bold italic underline | ' +
             'alignleft aligncenter alignright alignjustify | ' +
             'bullist numlist outdent indent | link image media | code preview fullscreen',
    automatic_uploads: true,

    // ✅ ВАЖНО: правильный путь к upload-image внутри ProductAdmin
    images_upload_url: '/admin/products/product/upload-image/',

    images_upload_handler: function (blobInfo) {
        return new Promise(function (resolve, reject) {
            const xhr = new XMLHttpRequest();
            xhr.withCredentials = true;
            xhr.open('POST', '/admin/products/product/upload-image/');
            xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));

            xhr.onload = function () {
                if (xhr.status !== 200) {
                    reject('HTTP Error: ' + xhr.status);
                    return;
                }

                let json;
                try {
                    json = JSON.parse(xhr.responseText);
                } catch (e) {
                    reject('Invalid JSON: ' + xhr.responseText);
                    return;
                }

                if (!json || typeof json.location !== 'string') {
                    reject('Invalid response: ' + xhr.responseText);
                    return;
                }

                resolve(json.location);
            };

            xhr.onerror = function () {
                reject('Image upload failed due to a network error.');
            };

            const formData = new FormData();
            formData.append('file', blobInfo.blob(), blobInfo.filename());
            xhr.send(formData);
        });
    },

    content_style: 'img { max-width: 100%; height: auto; display: block; margin: 0 auto; }'
});
