from .progress import (
    new_job,
    get as pg_get,
    update as pg_update,
    finish as pg_finish,
    cancel as pg_cancel,
    is_cancelled
)
import re
import random
import requests
from datetime import datetime
from django.shortcuts import render
from django.contrib.sites.models import Site
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.text import Truncator
import threading
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from products.models import Product, Category
from products.utils.images import save_url_as_webp

STEAM_API_URL = "https://store.steampowered.com/api/appdetails"
LIMIT_SCREENSHOTS = 3


# ────────────────────────────────
# ⚙️ Вспомогательные функции
# ────────────────────────────────

def _convert_in_background(product_id: int, logo_url: str | None, screenshots: list[str] | None):
    try:
        product = Product.objects.filter(id=product_id).first()
        if not product:
            return
        # реальная запись в модель
        _attach_webp_assets(product, logo_url=logo_url, screenshot_urls=screenshots)
    finally:
        # корректно закрываем соединение БД в потоке
        try:
            connection.close()
        except Exception:
            pass


def _attach_webp_assets(product, logo_url: str | None, screenshot_urls: list[str] | None):
    updated_fields = []

    # логотип
    if logo_url:
        try:
            saved = save_url_as_webp(logo_url, base_dir='logos')
            if hasattr(product, 'logo_file'):
                product.logo_file = saved["path"]  # сохраняем путь для ImageField
                updated_fields.append('logo_file')
            elif hasattr(product, 'logo_url'):
                product.logo_url = saved["url"]
                updated_fields.append('logo_url')
        except Exception:
            pass  # не роняем парсер из-за картинки

    # скриншоты
    local_urls = []
    for idx, s_url in enumerate((screenshot_urls or [])[:LIMIT_SCREENSHOTS]):
        try:
            saved = save_url_as_webp(s_url, base_dir='screenshots', base_name=f'screenshot-{idx + 1}')
            local_urls.append(saved["url"])
        except Exception:
            continue

    if local_urls and hasattr(product, 'screenshots'):
        product.screenshots = local_urls
        updated_fields.append('screenshots')

    if updated_fields:
        product.save(update_fields=updated_fields)


def get_current_site_from_request(request):
    site_id = (
            request.GET.get("site")
            or request.POST.get("site")
            or request.session.get("current_site_id")
    )
    if site_id and str(site_id).isdigit():
        return Site.objects.filter(id=site_id).first()
    return Site.objects.first()


def safe_steam_request(url: str):
    """Безопасный GET-запрос к Steam API с проверкой формата ответа"""
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if not isinstance(data, dict):
            print(f"⚠ Steam API вернул не dict: {type(data).__name__}")
            return {}
        return data
    except Exception as e:
        print(f"❌ Ошибка Steam API: {e}")
        return {}


def fetch_steam_ids_by_mode(mode: str, request):
    """Возвращает список уникальных Steam ID для парсинга"""

    # 1️⃣ Ручной ввод
    if mode == "manual":
        steam_ids = request.POST.get("steam_ids", "")
        raw_items = re.split(r"[\n,]+", steam_ids)
        return [
            re.search(r'/app/(\d+)', x).group(1)
            if x.startswith("http") and re.search(r'/app/(\d+)', x)
            else x.strip()
            for x in raw_items if x.strip()
        ]

    # 2️⃣ Случайная выборка
    elif mode == "random":
        target_count = int(request.POST.get("random_count", 10))

        resp = safe_steam_request("https://api.steampowered.com/ISteamApps/GetAppList/v2/")
        apps = resp.get("applist", {}).get("apps", [])
        if not isinstance(apps, list) or not apps:
            return []

        steam_ids = set()
        attempts = 0
        max_attempts = target_count * 100  # большой запас для добора

        while len(steam_ids) < target_count and attempts < max_attempts:
            attempts += 1
            app = random.choice(apps)
            appid = app.get("appid")
            if not appid or str(appid) in steam_ids:
                continue

            details = safe_steam_request(f"{STEAM_API_URL}?appids={appid}&cc=us&l=en")
            data = details.get(str(appid), {})
            if isinstance(data, dict) and data.get("success") and isinstance(data.get("data"), dict):
                steam_ids.add(str(appid))

        return list(steam_ids)[:target_count]

    return []


def parse_steam_game(steam_id: str, request=None):
    """Парсит приложение (игру/DLC/приложение) по Steam ID"""
    data = safe_steam_request(f"{STEAM_API_URL}?appids={steam_id}&cc=us&l=en")

    if not isinstance(data, dict):
        raise ValueError(
            f"Steam API вернул неожиданный тип данных ({type(data).__name__}) для {steam_id}"
        )

    app_data = data.get(str(steam_id))
    if not isinstance(app_data, dict):
        raise ValueError(
            f"Steam API вернул некорректный объект для {steam_id}: {type(app_data).__name__}"
        )

    if not app_data.get("success"):
        raise ValueError(f"Steam API не вернул данные для {steam_id} (success=False)")

    game = app_data.get("data")
    if not isinstance(game, dict):
        raise ValueError(
            f"Steam API вернул некорректный формат поля data ({type(game).__name__}) для {steam_id}"
        )

    # ── Нормализации ──
    for key in ["genres", "categories", "publishers", "developers"]:
        val = game.get(key, [])
        if isinstance(val, list):
            game[key] = [v.get("description") if isinstance(v, dict) else str(v) for v in val]
        elif isinstance(val, str):
            game[key] = [val]
        else:
            game[key] = []

    title = game.get("name", "").strip()
    if not title:
        raise ValueError(f"Не удалось получить название продукта для Steam ID {steam_id}")

    try:
        required_age = int(game.get("required_age") or 0)
    except Exception:
        required_age = 0

    release_date_raw = game.get("release_date", {}).get("date", "")
    release_date = None
    for fmt in ("%b %d, %Y", "%d %b, %Y", "%B %d, %Y"):
        try:
            release_date = datetime.strptime(release_date_raw, fmt).date()
            break
        except Exception:
            continue

    publishers = [p.strip() for p in game.get("publishers", [])]
    developers = [d.strip() for d in game.get("developers", [])]

    pc_reqs = game.get("pc_requirements", {})
    min_req_html = ""
    if isinstance(pc_reqs, dict):
        min_req_html = pc_reqs.get("minimum", "")
    elif isinstance(pc_reqs, list) and pc_reqs:
        first = pc_reqs[0]
        if isinstance(first, dict):
            min_req_html = first.get("minimum", "")

    min_os = min_processor = min_ram = min_graphics = min_storage = min_additional = ""

    if isinstance(min_req_html, str) and min_req_html.strip():
        cleaned = re.sub(r"<br\s*/?>", "\n", min_req_html, flags=re.I)
        cleaned = re.sub(r"<[^>]+>", "", cleaned).strip()
        for line in cleaned.splitlines():
            line_lower = line.lower()
            if "os" in line_lower:
                min_os = line.split(":", 1)[-1].strip()
            elif "processor" in line_lower:
                min_processor = line.split(":", 1)[-1].strip()
            elif "memory" in line_lower or "ram" in line_lower:
                min_ram = line.split(":", 1)[-1].strip()
            elif "graphics" in line_lower or "video" in line_lower:
                min_graphics = line.split(":", 1)[-1].strip()
            elif "storage" in line_lower or "hdd" in line_lower:
                min_storage = line.split(":", 1)[-1].strip()
            else:
                line_clean = line.replace("Minimum:", "").strip()
                if line_clean:
                    min_additional += line_clean + " "

    screenshots = [s.get("path_full") for s in game.get("screenshots", []) if isinstance(s, dict)]

    # Категория
    category_name = "Steam Product"
    if game["genres"]:
        category_name = game["genres"][0]
    elif game["categories"]:
        category_name = game["categories"][0]

    category, _ = Category.objects.get_or_create(name=category_name, type="game")
    site = get_current_site_from_request(request) if request else Site.objects.first()

    # ── Создание/обновление продукта ──
    product, _ = Product.objects.update_or_create(
        steam_id=steam_id,
        site=site,
        defaults={
            "title": title,
            "is_active": True,
            "required_age": required_age,
            "release_date": release_date,
            "category": category,
            "publishers": publishers,
            "developers": developers,
            "logo_url": game.get("header_image", ""),
            "screenshots": screenshots,
            "steam_url": f"https://store.steampowered.com/app/{steam_id}/",
            "min_os": Truncator(min_os).chars(300),
            "min_processor": Truncator(min_processor).chars(300),
            "min_ram": Truncator(min_ram).chars(300),
            "min_graphics": Truncator(min_graphics).chars(300),
            "min_storage": Truncator(min_storage).chars(300),
            "min_additional": Truncator(min_additional.strip()).chars(300),
        }
    )

    # ⬇️ Конвертацию уносим в бэкграунд, чтобы не блокировать ответ админке
    threading.Thread(
        target=_convert_in_background,
        args=(product.id, game.get("header_image", ""), screenshots[:LIMIT_SCREENSHOTS]),
        daemon=True,
    ).start()
    return product


def _parse_worker(job_id: str, request, parse_mode: str, target_count: int):
    attempted = 0
    added = 0
    errors = 0
    try:
        current_site = get_current_site_from_request(request)
        steam_ids = fetch_steam_ids_by_mode(parse_mode, request)
        steam_ids = list(dict.fromkeys(steam_ids))
        if parse_mode != "random":
            steam_ids = steam_ids[: target_count * 5]

        total = min(len(steam_ids), target_count)
        if total == 0:
            pg_update(job_id, processed=0, added=0, errors=0, msg="Нет ID для парсинга")
            return

        existing_ids = set(Product.objects.filter(site=current_site).values_list("steam_id", flat=True))

        for steam_id in steam_ids:
            if attempted >= target_count:
                break
            # ❗ проверка отмены перед обработкой ID
            if is_cancelled(job_id):
                pg_update(job_id, processed=attempted, added=added, errors=errors,
                          msg="Отменено пользователем. Завершение…")
                break

            attempted += 1  # начали попытку

            if steam_id in existing_ids:
                pg_update(job_id, processed=attempted, added=added, errors=errors,
                          msg=f"Пропущено: {steam_id} уже существует")
                continue

            try:
                product = parse_steam_game(steam_id, request=request)
                if not product or not getattr(product, "id", None):
                    raise ValueError("empty product")
                existing_ids.add(steam_id)
                added += 1
                title = getattr(product, "title", "(без названия)")
                pg_update(job_id, processed=attempted, added=added, errors=errors,
                          msg=f"OK: {steam_id} — {title}")
            except Exception as e:
                errors += 1
                pg_update(job_id, processed=attempted, added=added, errors=errors,
                          msg=f"ERR: {steam_id} ({e})")

        # финальное сообщение: различаем нормальное завершение и отмену
        if is_cancelled(job_id):
            pg_update(job_id, processed=attempted, added=added, errors=errors,
                      msg=f"Отменено. Итог: добавлено {added}, ошибок {errors}")
            pg_finish(job_id, status="cancelled")
        else:
            pg_update(job_id, processed=total, added=added, errors=errors,
                      msg=f"Готово: добавлено {added}, ошибок {errors}")
            pg_finish(job_id, status="done")
    except Exception as e:
        # аварийное завершение (на всякий)
        pg_update(job_id, msg=f"Неожиданная ошибка: {e}")
        pg_finish(job_id, status="done")


@csrf_exempt
@staff_member_required
def parse_steam_start(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    parse_mode = request.POST.get("parse_mode", "manual")
    target_count = int(request.POST.get("random_count", 10)) if parse_mode == "random" else 10

    job_id = new_job(total=target_count)
    t = threading.Thread(target=_parse_worker, args=(job_id, request, parse_mode, target_count), daemon=True)
    t.start()

    return JsonResponse({"job_id": job_id})


@staff_member_required
def parse_steam_status(request, job_id: str):
    data = pg_get(job_id)
    if not data:
        return JsonResponse({"error": "unknown job"}, status=404)
    return JsonResponse(data)


@csrf_exempt
@staff_member_required
def parse_steam_cancel(request, job_id: str):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    pg_cancel(job_id)  # помечаем отмену; воркер увидит и завершится
    return JsonResponse({"ok": True})


# ────────────────────────────────
# 🖥️ Админ-обёртка
# ────────────────────────────────

@staff_member_required
def parse_steam_view(request):
    context = request.admin_site.each_context(request) if hasattr(request, 'admin_site') else {}
    context.update({
        "site_list": Site.objects.all(),
        "current_site": get_current_site_from_request(request),
    })
    return render(request, 'admin/products/parse_steam.html', context)
