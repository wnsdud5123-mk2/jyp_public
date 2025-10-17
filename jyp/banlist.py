# jyp/banlist.py
from __future__ import annotations
import os

# 공유 폴더 경로
BAN_DIR = r"\\10.2.0.113\홍보마케팅\_개인폴더_\이준영\터치X"
BAN_FILE_NOCADDY = os.path.join(BAN_DIR, "노캐디 금지목록.txt")
BAN_FILE_FIVE    = os.path.join(BAN_DIR, "5인플레이 금지목록.txt")

_DEFAULT_NOCADDY = ["홍명열","최연홍","김청엽","이관승","고민서","이명신"]
_DEFAULT_FIVE = [
    "박선철","최경진","조국정","심남열","서영주","성구현","이남진","윤순정",
    "김정식","권동진","김동현","신인호","석봉환","박진석","김지성","최기수",
    "박우세","서문억","나영수","김진수","최성관","차준관","오기택","김환태",
    "주훈종","조경희","강용운","김정수","박근용","박정진","이제휴"
]

노캐디금지목록: set[str] = set(_DEFAULT_NOCADDY)
오인플금지목록: set[str] = set(_DEFAULT_FIVE)

def _read_lines(path: str) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip()]
    except Exception:
        return []

def _write_lines(path: str, names: set[str]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for name in sorted(names):
            f.write(name + "\n")

def reload_from_disk() -> None:
    """공유 폴더에서 다시 읽어 전역 set을 갱신."""
    global 노캐디금지목록, 오인플금지목록
    n = _read_lines(BAN_FILE_NOCADDY)
    f = _read_lines(BAN_FILE_FIVE)
    if n: 노캐디금지목록 = set(n)
    if f: 오인플금지목록 = set(f)

def persist(kind: str) -> None:
    """'nocaddy' | 'five'"""
    if kind == "nocaddy":
        _write_lines(BAN_FILE_NOCADDY, 노캐디금지목록)
    else:
        _write_lines(BAN_FILE_FIVE, 오인플금지목록)

# 모듈 import 시 한 번 읽기
reload_from_disk()
