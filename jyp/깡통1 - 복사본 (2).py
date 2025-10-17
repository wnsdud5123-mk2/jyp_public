# gas_ping_test.py
# GAS Web App "ping" 통신 확인용 스크립트

import time
import hashlib
import urllib.parse
import requests

# ① 여기에 네가 배포한 /exec 주소를 넣어줘
GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzeksDSNknEUR-PuXwjdrFlbRQMBm4PRITYKI1kf2RzGFSp_YGxZgMZgwiiTich4cqA/exec"

# ② GAS에서 서명 검증을 쓴다면 비밀키를 넣고, 안 쓰면 빈문자("") 그대로 두면 됨
GAS_SECRET = ""  # 예: "super-secret"  (미사용이면 "")

def make_signature(secret: str, when: int, method: str, action: str) -> str:
    """
    GAS의 checkSig_ 규칙과 맞춰야 합니다.
    예시: sha256( secret + '|' + when + '|' + method + '|' + action )
    """
    raw = f"{secret}|{when}|{method.upper()}|{action}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def ping():
    params = {"action": "ping"}

    if GAS_SECRET:
        when = int(time.time())
        params["when"] = str(when)
        params["sig"] = make_signature(GAS_SECRET, when, "GET", "ping")

    # 디버깅용: 실제 요청 URL 미리 보기
    print("REQUEST:", GAS_WEBAPP_URL + "?" + urllib.parse.urlencode(params, doseq=True))

    r = requests.get(GAS_WEBAPP_URL, params=params, timeout=10)
    print("STATUS :", r.status_code)
    print("TEXT   :", r.text)

    try:
        print("JSON   :", r.json())
    except Exception:
        pass

if __name__ == "__main__":
    try:
        ping()
    except requests.RequestException as e:
        print("NETWORK ERROR:", e)
