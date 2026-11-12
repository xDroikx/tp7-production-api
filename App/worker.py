import json
import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Intentar conectar con Redis real; si no existe, usar fakeredis
try:
    _real_client = redis.Redis(
        host=REDIS_HOST, 
        port=REDIS_PORT, 
        decode_responses=True, 
        socket_connect_timeout=1
    )
    _real_client.ping()
    redis_client = _real_client
    print("🟢 Conectado exitosamente al servidor Redis local.")
except Exception:
    import fakeredis
    print("🟡 Redis local no detectado. Utilizando emulador en memoria (fakeredis).")
    redis_client = fakeredis.FakeRedis(decode_responses=True)

TASK_PREFIX = "task:"

def save_task(task_id: str, data: dict):
    """Guarda o actualiza el estado de una tarea."""
    redis_client.set(f"{TASK_PREFIX}{task_id}", json.dumps(data), ex=86400)

def get_task(task_id: str) -> dict:
    """Recupera la tarea guardada."""
    raw = redis_client.get(f"{TASK_PREFIX}{task_id}")
    if not raw:
        return None
    return json.loads(raw)