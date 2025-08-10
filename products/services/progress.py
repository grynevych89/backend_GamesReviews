import uuid
from django.core.cache import cache

TTL = 60 * 30  # 30 минут

def _key(job_id: str) -> str:
    return f"parse_job:{job_id}"

def new_job(total: int) -> str:
    job_id = uuid.uuid4().hex
    cache.set(_key(job_id), {
        "total": int(total),
        "processed": 0,
        "added": 0,
        "errors": 0,
        "items": [],
        "done": False,
        "cancel": False,
        "status": "running",
    }, TTL)
    return job_id

def get(job_id: str) -> dict | None:
    return cache.get(_key(job_id))

def update(job_id: str, *, processed=None, added=None, errors=None, msg: str | None = None):
    data = cache.get(_key(job_id))
    if not data:
        return
    if processed is not None: data["processed"] = int(processed)
    if added is not None:     data["added"] = int(added)
    if errors is not None:    data["errors"] = int(errors)
    if msg:
        items = data.get("items", [])
        items.append(msg)
        data["items"] = items[-10:]
    cache.set(_key(job_id), data, TTL)

def finish(job_id: str, *, status: str | None = None):
    data = cache.get(_key(job_id)) or {}
    data["done"] = True
    if status:
        data["status"] = status
    elif data.get("status") == "cancelled":
        # если уже отменён — оставим cancelled
        pass
    else:
        data["status"] = "done"
    cache.set(_key(job_id), data, TTL)

# --- отмена ---
def cancel(job_id: str):
    """Пометить задачу как отменённую (воркер увидит флаг и сам завершится)."""
    data = cache.get(_key(job_id))
    if not data:
        return
    data["cancel"] = True
    data["status"] = "cancelled"
    cache.set(_key(job_id), data, TTL)

def is_cancelled(job_id: str) -> bool:
    data = cache.get(_key(job_id)) or {}
    return bool(data.get("cancel"))
