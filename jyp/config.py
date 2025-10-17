# jyp/config.py
import os, sys
# 템플릿 공유파일 경로 (환경변수 우선)
TEMPLATE_PATH = os.environ.get(
    "JYP_TEMPLATE_PATH",
    r"\\10.2.0.113\홍보마케팅\_개인폴더_\이준영\터치X\JYP_templates.json"
)

def _project_root():
    # jyp/ 밑이라서 한 단계 위가 프로젝트 루트
    here = os.path.dirname(__file__)
    return os.path.dirname(here)

# 실행/배포 모두에서 자원 경로 찾기
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS  # PyInstaller
else:
    BASE_DIR = _project_root()

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
HUM_PATH   = os.path.join(ASSETS_DIR, "hum.jpg")

# 공통 상수
PLACEHOLDER = "여기에 이름입력"

# 테마
기본테마 = {
    "배경": "#f8fff4",
    "라벨글자": "#2e7d32",
    "입력창배경": "white",
    "출력창배경": "#f1f8e9"
}
씹덕테마 = {
    "배경": "#fff0fb",
    "라벨글자": "#e91e63",
    "입력창배경": "#fff7fc",
    "출력창배경": "#fff0f5"
}
# --- JYP + GAS 연동 ---
API_URL = os.environ.get("JYP_API_URL") or "https://script.google.com/macros/s/AKfycbzeksDSNknEUR-PuXwjdrFlbRQMBm4PRITYKI1kf2RzGFSp_YGxZgMZgwiiTich4cqA/exec"
API_SECRET = os.environ.get("JYP_API_SECRET") or "SECRET"
API_TIMEOUT = 8  # 초

# --- GAS 연결 설정 ---
GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzeksDSNknEUR-PuXwjdrFlbRQMBm4PRITYKI1kf2RzGFSp_YGxZgMZgwiiTich4cqA/exec"  # 네 배포 URL
GAS_SECRET = "wnsduddlsmstlqejrdlek~!!"  # 지금은 비워둬도 동작. 나중에 Script Properties에 같은 값 넣고 서명검증 켜면 됨
