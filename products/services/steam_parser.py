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

from products.models import Product, Category

# ────────────────────────────────
# ⚙️ Константы
# ────────────────────────────────

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

        # Загружаем список всех приложений
        resp = requests.get(
            "https://api.steampowered.com/ISteamApps/GetAppList/v2/",
            timeout=15
        ).json()
        apps = resp.get("applist", {}).get("apps", [])
        if not apps:
            return []

        steam_ids = set()
        attempts = 0
        max_attempts = target_count * 200  # большой запас

        while len(steam_ids) < target_count and attempts < max_attempts:
            attempts += 1
            app = random.choice(apps)
            appid = app.get("appid")
            if not appid or str(appid) in steam_ids:
                continue

            # Проверяем, что это игра
            try:
                details = requests.get(
                    f"{STEAM_API_URL}?appids={appid}&cc=us&l=en",
                    timeout=6
                ).json()
                data = details.get(str(appid), {})
                if data.get("success") and data.get("data", {}).get("type") == "game":
                    steam_ids.add(str(appid))
            except requests.RequestException:
                continue

        return list(steam_ids)[:target_count]

    return []


def parse_steam_game(steam_id: str, request=None):
    """Парсит игру по Steam ID через Steam API"""
    url = f"{STEAM_API_URL}?appids={steam_id}&cc=us&l=en"
    resp = requests.get(url, timeout=10)
    data = resp.json()

    if not data.get(str(steam_id), {}).get("success"):
        return None

    game = data[str(steam_id)]["data"]

    title = game.get("name", "").strip()
    required_age = int(game.get("required_age") or 0)

    # Парсинг даты релиза
    release_date_raw = game.get("release_date", {}).get("date", "")
    release_date = None
    for fmt in ("%b %d, %Y", "%d %b, %Y", "%B %d, %Y"):
        try:
            release_date = datetime.strptime(release_date_raw, fmt).date()
            break
        except:
            continue

    # Минимальные требования
    publishers = [p.strip() for p in game.get("publishers", [])]
    min_req_html = game.get("pc_requirements", {}).get("minimum", "")
    min_os = min_processor = min_ram = min_graphics = min_storage = min_additional = ""

    if min_req_html:
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

    screenshots = [s["path_full"] for s in game.get("screenshots", [])]
    category, _ = Category.objects.get_or_create(name="Steam Game", type="game")
    site = get_current_site_from_request(request) if request else Site.objects.first()

    product, _ = Product.objects.update_or_create(
        steam_id=steam_id,
        site=site,  # 🔹 теперь учитываем сайт
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
            "min_os": min_os,
            "min_processor": min_processor,
            "min_ram": min_ram,
            "min_graphics": min_graphics,
            "min_storage": min_storage,
            "min_additional": min_additional.strip(),
        }
    )

    return product


# ────────────────────────────────
# 🖥️ Админ-обёртка
# ────────────────────────────────

@staff_member_required
def parse_steam_view(request):
    """Страница парсинга игр со Steam в админке"""
    parsed_count = 0
    errors = []

    if request.method == "POST":
        parse_mode = request.POST.get("parse_mode", "manual")
        target_count = int(request.POST.get("random_count", 10)) if parse_mode == "random" else 10

        # 1️⃣ Определяем текущий сайт
        current_site = get_current_site_from_request(request)

        # 2️⃣ Получаем список Steam ID
        steam_ids = fetch_steam_ids_by_mode(parse_mode, request)
        steam_ids = list(dict.fromkeys(steam_ids))  # убираем дубликаты

        if parse_mode != "random":
            steam_ids = steam_ids[: target_count * 5]  # запас для топов

        if not steam_ids:
            messages.warning(request, "⚠ Не найдено ни одного Steam ID для парсинга")
            return redirect('admin:products_product_parse_steam')

        # 3️⃣ Существующие игры только для текущего сайта
        existing_ids = set(
            Product.objects.filter(site=current_site).values_list("steam_id", flat=True)
        )

        # 4️⃣ Парсинг
        added_products = []
        skipped_products = []

        for steam_id in steam_ids:
            if parsed_count >= target_count:
                break

            existing_product = Product.objects.filter(
                steam_id=steam_id, site=current_site
            ).first()

            if existing_product:
                skipped_products.append(f"«{existing_product.title}» (ID {steam_id})")
                continue

            try:
                product = parse_steam_game(steam_id, request=request)
                if product:
                    parsed_count += 1
                    existing_ids.add(steam_id)
                    added_products.append(f"«{product.title}» (ID {steam_id})")
                else:
                    errors.append(steam_id)
            except Exception as e:
                errors.append(steam_id)
                print(f"❌ Ошибка при парсинге {steam_id}: {e}")

        # 5️⃣ Сообщения о результатах
        if skipped_products:
            details = "; ".join(skipped_products[:5])
            if len(skipped_products) > 5:
                details += f" и ещё {len(skipped_products)-5}…"

            messages.warning(
                request,
                mark_safe(
                    f"⚠ Пропущено {len(skipped_products)} игр, так как они уже существуют для текущего сайта."
                    + f"<br><small>{details}</small>"
                )
            )

        if parsed_count:
            details = "; ".join(added_products[:5])
            if len(added_products) > 5:
                details += f" и ещё {len(added_products)-5}…"

            messages.success(
                request,
                mark_safe(
                    f"✔ Успешно добавлено {parsed_count} новых игр со Steam"
                    + (f" (ошибки: {len(errors)})" if errors else "")
                    + f"<br><small>{details}</small>"
                )
            )

        if errors:
            messages.error(
                request,
                f"Не удалось спарсить: {', '.join(errors[:10])}" +
                ("..." if len(errors) > 10 else "")
            )

        # 6️⃣ Редирект на текущий сайт
        site_id = current_site.id if current_site else ""
        url = reverse('admin:products_product_changelist')
        if site_id:
            url += f"?site={site_id}"
        return redirect(url)

    # GET-запрос → форма
    context = request.admin_site.each_context(request) if hasattr(request, 'admin_site') else {}
    return render(request, 'admin/products/parse_steam.html', context)
