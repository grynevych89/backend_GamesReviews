import os
import re
from io import BytesIO
from datetime import datetime

import requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image
from os.path import basename, splitext

SAFE_NAME_RE = re.compile(r'[^A-Za-z0-9._-]+')


def _safe_base_from_name(name: str) -> str:
    base, _ext = splitext(basename(name or 'image'))
    safe = SAFE_NAME_RE.sub('-', base).strip('-_.')
    return safe or 'image'


def _ensure_webp_bytes(file_or_bytes) -> bytes:
    """
    Принимает file-like (InMemoryUploadedFile, BytesIO) или bytes,
    возвращает webp-байты (quality=85, method=6).
    """
    if isinstance(file_or_bytes, (bytes, bytearray)):
        src = BytesIO(file_or_bytes)
    else:
        # file-like
        src = file_or_bytes

    img = Image.open(src)
    # оставляем alpha, если RGBA; другие режимы приводим к RGB
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')

    buf = BytesIO()
    img.save(buf, format='WEBP', quality=80, method=4)
    buf.seek(0)
    return buf.read()


def _unique_target_path(base_dir: str, base_name: str) -> str:
    """
    Возвращает уникальный путь вида:
    {base_dir}/{YYYY}/{MM}/{DD}/{base_name}.webp (или -1.webp, -2.webp ...)
    """
    date_path = datetime.now().strftime('%Y/%m/%d')
    target_dir = os.path.join(base_dir, date_path)

    filename = f'{base_name}.webp'
    candidate = os.path.join(target_dir, filename)
    counter = 1
    while default_storage.exists(candidate):
        filename = f'{base_name}-{counter}.webp'
        candidate = os.path.join(target_dir, filename)
        counter += 1
    return candidate


def save_upload_as_webp(upload, base_dir: str = 'uploads') -> dict:
    """
    Конвертирует загруженный файл в WEBP и сохраняет.
    Сохраняет оригинальное имя (без хэшей), делает уникализацию -1, -2...
    Возвращает dict: {"path": saved_path, "url": absolute_or_media_url}
    """
    safe_base = _safe_base_from_name(getattr(upload, 'name', 'image'))
    webp_bytes = _ensure_webp_bytes(upload)
    target_path = _unique_target_path(base_dir, safe_base)

    saved_path = default_storage.save(target_path, ContentFile(webp_bytes))
    return {"path": saved_path, "url": default_storage.url(saved_path)}


def save_url_as_webp(url: str, base_dir: str = 'uploads', base_name: str | None = None, timeout: int = 8):
    resp = requests.get(url, stream=True, timeout=timeout)
    resp.raise_for_status()
    content = resp.content

    if not base_name:
        # достаём имя из url-пути
        url_name = os.path.basename(url.split('?', 1)[0].split('#', 1)[0]) or 'image'
        base_name, _ = os.path.splitext(url_name)
    safe_base = _safe_base_from_name(base_name)

    webp_bytes = _ensure_webp_bytes(content)
    target_path = _unique_target_path(base_dir, safe_base)

    saved_path = default_storage.save(target_path, ContentFile(webp_bytes))
    return {"path": saved_path, "url": default_storage.url(saved_path)}
