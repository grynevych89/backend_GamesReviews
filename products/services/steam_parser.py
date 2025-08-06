import re
import random
import requests
from datetime import datetime
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.sites.models import Site
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

from products.models import Product, Category

STEAM_API_URL = "https://store.steampowered.com/api/appdetails"

# ────────────────────────────────
# ⚙️ Вспомогательные функции
# ────────────────────────────────

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
        max_attempts = target_count * 200  # большой запас для добора

        while len(steam_ids) < target_count and attempts < max_attempts:
            attempts += 1
            app = random.choice(apps)
            appid = app.get("appid")
            if not appid or str(appid) in steam_ids:
                continue

            # Проверяем, что приложение доступно (любое: игра, DLC, софт)
            details = safe_steam_request(f"{STEAM_API_URL}?appids={appid}&cc=us&l=en")
            data = details.get(str(appid), {})
            if isinstance(data, dict) and data.get("success") and isinstance(data.get("data"), dict):
                steam_ids.add(str(appid))

        return list(steam_ids)[:target_count]

    return []


def parse_steam_game(steam_id: str, request=None):
    """Парсит приложение (игру/DLC/приложение) по Steam ID"""
    # 🔹 Запрос к Steam API
    data = safe_steam_request(f"{STEAM_API_URL}?appids={steam_id}&cc=us&l=en")

    # 🔹 Проверяем основной ответ
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

    # ────────────────────────────────
    # 📦 Нормализация полей
    # ────────────────────────────────
    for key in ["genres", "categories", "publishers", "developers"]:
        val = game.get(key, [])
        if isinstance(val, list):
            game[key] = [v.get("description") if isinstance(v, dict) else str(v) for v in val]
        elif isinstance(val, str):
            game[key] = [val]
        else:
            game[key] = []

    # ────────────────────────────────
    # 📛 Название
    # ────────────────────────────────
    title = game.get("name", "").strip()
    if not title:
        raise ValueError(f"Не удалось получить название продукта для Steam ID {steam_id}")

    # ────────────────────────────────
    # 🔞 Возрастное ограничение
    # ────────────────────────────────
    try:
        required_age = int(game.get("required_age") or 0)
    except Exception:
        required_age = 0

    # ────────────────────────────────
    # 📅 Дата релиза
    # ────────────────────────────────
    release_date_raw = game.get("release_date", {}).get("date", "")
    release_date = None
    for fmt in ("%b %d, %Y", "%d %b, %Y", "%B %d, %Y"):
        try:
            release_date = datetime.strptime(release_date_raw, fmt).date()
            break
        except Exception:
            continue

    # ────────────────────────────────
    # 🖥 Минимальные требования
    # ────────────────────────────────
    publishers = [p.strip() for p in game.get("publishers", [])]

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

    # ────────────────────────────────
    # 🏷 Категория по жанрам или категориям Steam
    # ────────────────────────────────
    category_name = "Steam Product"
    if game["genres"]:
        category_name = game["genres"][0]
    elif game["categories"]:
        category_name = game["categories"][0]

    category, _ = Category.objects.get_or_create(name=category_name, type="game")
    site = get_current_site_from_request(request) if request else Site.objects.first()

    # ────────────────────────────────
    # 💾 Создание или обновление продукта
    # ────────────────────────────────
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

    return product


# ────────────────────────────────
# 🖥️ Админ-обёртка
# ────────────────────────────────

@staff_member_required
def parse_steam_view(request):
    """Страница парсинга приложений Steam в админке"""
    parsed_count = 0
    errors = []

    if request.method == "POST":
        parse_mode = request.POST.get("parse_mode", "manual")
        target_count = int(request.POST.get("random_count", 10)) if parse_mode == "random" else 10
        current_site = get_current_site_from_request(request)

        # Получаем список Steam ID
        steam_ids = fetch_steam_ids_by_mode(parse_mode, request)
        steam_ids = list(dict.fromkeys(steam_ids))  # убираем дубликаты

        if parse_mode != "random":
            steam_ids = steam_ids[: target_count * 5]

        if not steam_ids:
            messages.warning(request, "⚠ Не найдено ни одного Steam ID для парсинга")
            return redirect('admin:products_product_parse_steam')

        existing_ids = set(Product.objects.filter(site=current_site).values_list("steam_id", flat=True))
        added_products = []

        for steam_id in steam_ids:
            if parsed_count >= target_count:
                break

            if steam_id in existing_ids:
                existing_product = Product.objects.filter(steam_id=steam_id, site=current_site).first()
                if existing_product:
                    messages.warning(
                        request,
                        f"Игра «{existing_product.title}» (Steam ID {steam_id}) уже существует для текущего сайта и была пропущена."
                    )
                continue

            try:
                product = parse_steam_game(steam_id, request=request)
                parsed_count += 1
                existing_ids.add(steam_id)
                added_products.append(f"«{product.title}» (ID {steam_id})")
            except Exception as e:
                errors.append(f"{steam_id} ({str(e)})")
                print(f"❌ Ошибка при парсинге {steam_id}: {e}")

        # Сообщения
        if parsed_count:
            details = "; ".join(added_products[:5])
            if len(added_products) > 5:
                details += f" и ещё {len(added_products)-5}…"

            messages.success(
                request,
                mark_safe(
                    f"✔ Успешно добавлено {parsed_count} новых продуктов со Steam"
                    + (f" (ошибки: {len(errors)})" if errors else "")
                    + f"<br><small>{details}</small>"
                )
            )

        if errors:
            messages.error(
                request,
                f"Не удалось спарсить: {', '.join(errors[:10])}" + ("..." if len(errors) > 10 else "")
            )

        url = reverse('admin:products_product_changelist')
        if current_site:
            url += f"?site={current_site.id}"
        return redirect(url)

    # GET-запрос → форма
    context = request.admin_site.each_context(request) if hasattr(request, 'admin_site') else {}
    context.update({
        "site_list": Site.objects.all(),
        "current_site": get_current_site_from_request(request),
    })
    return render(request, 'admin/products/parse_steam.html', context)
