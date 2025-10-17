# jyp/templates.py
from __future__ import annotations
import json, os
from typing import Dict, Any, List, Tuple
from .config import TEMPLATE_PATH
from .cloud import fetch_templates

# ───────────────── 기본(내장) 템플릿 ─────────────────
_DEFAULT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "예약확정문자": {
        "fields": [
            ("예약자","name"),
            ("예약일자","날짜","date"),
            ("코스","코스"),
            ("시간","시간","time"),
        ],
        "format":
            "[장수골프리조트]\n"
            "예약이 완료 되었습니다.\n"
            "라운드 전 내용 확인해 주시기 바랍니다.\n"
            "\n"
            "▷ 예약정보\n"
            "· 예약자명 : {name}님\n"
            "· 예약일자 : {날짜}\n"
            "· 비고 : {코스} / {시간} / 18홀\n"
            " - ▷ 셀프체크인\n"
            "당 클럽은 빠르고, 편리한 키오스크로 운영중입니다. \n"
            "원활한 셀프체크인을 위해 내장객 명단을 문자로 보내주세요. \n"
            "(예약자명 + 내장객명단 / 남,여)\n"
            "보내실 곳 010-7245-1760\n"
            "\n"
            "▷ 취소가능기한\n"
            "· {날짜-3} 23:59\n"
            "\n"
            "▷ 주의사항\n"
            "취소가능기한 이후 취소시 위약금이 발생 할 수 있으며, 골프예약 서비스 이용에 제약을 받을 수 있습니다."
    },
    "딜레이 안내문자": {
        "fields": [("시간","시간")],
        "format":
            """[장수골프리조트 이용안내]
안녕하세요.
장수골프리조트입니다.

금일 1부 풀팀으로 인해서 
{{?시간:대기시간 지연 {시간}분 티업 딜레이가 발생할 수도 있습니다.|티업 딜레이가 발생할 수도 있습니다.}}
고객님의 너그러운 양해부탁드립니다.

감사합니다."""
    }
}

# 요일 맵
요일표 = {"Mon":"월","Tue":"화","Wed":"수","Thu":"목","Fri":"금","Sat":"토","Sun":"일"}

# 실제 사용 레지스트리
TEMPLATES: Dict[str, Dict[str, Any]] = {}
TEMPLATES.update(_DEFAULT_TEMPLATES)

# ──────────────── 파일 I/O 유틸 ────────────────
def _read_file(path: str) -> Dict[str, Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    out: Dict[str, Dict[str, Any]] = {}
    for name, spec in raw.items():
        fields: List[Tuple[str, str, *tuple]] = []
        for item in spec.get("fields", []):
            if isinstance(item, (list, tuple)):
                fields.append(tuple(item))  # ["라벨","키","type?"] → tuple
        out[name] = {"fields": fields, "format": spec.get("format", "")}
    return out

def persist() -> None:
    """현재 TEMPLATES를 로컬 JSON(TEMPLATE_PATH)으로 백업 저장."""
    path = TEMPLATE_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    serializable = {
        k: {"fields": [list(f) for f in v.get("fields", [])], "format": v.get("format", "")}
        for k, v in TEMPLATES.items()
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)

# ──────────────── 정합성 필터 ────────────────
def _sanitize(obj: Dict[str, Any]) -> Dict[str, Any]:
    """fields(list)와 format(str)이 있는 항목만 살려서 반환."""
    good: Dict[str, Dict[str, Any]] = {}
    for k, v in (obj or {}).items():
        if isinstance(v, dict) and isinstance(v.get("fields"), list) and isinstance(v.get("format"), str):
            good[k] = v
    return good

def _normalize_from_cloud(raw: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """GAS에서 온 dict를 내부 형식으로 정리."""
    out: Dict[str, Dict[str, Any]] = {}
    for name, spec in (raw or {}).items():
        fields: List[Tuple[str, str, *tuple]] = []
        for item in spec.get("fields", []):
            if isinstance(item, (list, tuple)):
                fields.append(tuple(item))
        out[name] = {"fields": fields, "format": spec.get("format", "")}
    return out

# ──────────────── 로드 진입점 ────────────────
def reload_from_cloud() -> bool:
    """GAS → (성공시) 로컬 백업까지 갱신."""
    try:
        js = fetch_templates()                 # dict
        clean = _sanitize(js)
        if clean:
            TEMPLATES.clear()
            TEMPLATES.update(_DEFAULT_TEMPLATES)
            TEMPLATES.update(_normalize_from_cloud(clean))
            # 원하면 백업 저장
            try:
                persist()
            except Exception:
                pass
            return True
    except Exception as e:
        print("GAS fetch fail:", e)
    return False

def reload_from_disk() -> bool:
    """
    이름은 유지하지만 실제 순서는:
    1) GAS 시도 → 실패 시
    2) 로컬 JSON 백업 시도 → 실패 시
    3) 기본 템플릿만 사용
    """
    # 1) GAS
    if reload_from_cloud():
        return True

    # 2) 로컬
    path = TEMPLATE_PATH
    if path and os.path.exists(path):
        try:
            local = _read_file(path)
            TEMPLATES.clear()
            TEMPLATES.update(_DEFAULT_TEMPLATES)
            TEMPLATES.update(local)
            return True
        except Exception as e:
            print("templates: local read fail ->", e)

    # 3) 기본만
    TEMPLATES.clear()
    TEMPLATES.update(_DEFAULT_TEMPLATES)
    return False
