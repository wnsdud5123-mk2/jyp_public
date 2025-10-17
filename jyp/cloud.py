# jyp/cloud.py  – GAS(ts+sig, Base64 HMAC-SHA256) 호환 버전
import time, hmac, hashlib, base64, json, requests
from .config import GAS_WEBAPP_URL, GAS_SECRET

def _make_sig(ts: int, body_text: str) -> str:
    # GAS checkSig_ 기반: base = f"{ts}\n{bodyText}"
    base = f"{ts}\n{body_text}".encode("utf-8")
    key  = GAS_SECRET.encode("utf-8")
    mac  = hmac.new(key, base, hashlib.sha256).digest()
    return base64.b64encode(mac).decode("ascii")

def _auth_params(ts: int, body_text: str):
    if not GAS_SECRET:
        # 서명 비활성(개발/테스트): ts/sig 없이
        return {}
    return {"ts": str(ts), "sig": _make_sig(ts, body_text)}

def gas_get(action: str, params: dict | None = None, timeout: int = 8):
    ts = int(time.time())
    body_text = ""  # GET은 빈 문자열
    q = {"action": action, **(params or {}), **_auth_params(ts, body_text)}
    r = requests.get(GAS_WEBAPP_URL, params=q, timeout=timeout)
    r.raise_for_status()
    return r.json()

def gas_post(action: str, payload: dict | None = None, timeout: int = 8):
    ts = int(time.time())
    body_text = json.dumps(payload or {}, ensure_ascii=False, separators=(",", ":"))
    q = {"action": action, **_auth_params(ts, body_text)}
    headers = {"Content-Type": "application/json; charset=utf-8"}
    r = requests.post(GAS_WEBAPP_URL, params=q, data=body_text.encode("utf-8"),
                      headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()

# ---- 고수준 API --------------------------------------------------------
def fetch_templates() -> dict:
    # GET /?action=templates
    return gas_get("templates")

def fetch_ban(kind: str) -> list[str]:
    # GET /?action=ban&kind=nocaddy|five → {kind, list:[...]}
    js = gas_get("ban", {"kind": kind})
    return js.get("list", [])

def update_templates(registry: dict) -> bool:
    # POST action=templates.update  body={...}
    js = gas_post("templates.update", registry)
    return bool(js.get("ok"))

def ban_add(kind: str, name: str) -> bool:
    js = gas_post("ban.add", {"kind": kind, "name": name})
    return bool(js.get("ok"))

def ban_remove(kind: str, name: str) -> bool:
    js = gas_post("ban.remove", {"kind": kind, "name": name})
    return bool(js.get("ok"))
