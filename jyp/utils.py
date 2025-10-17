# jyp/utils.py
from __future__ import annotations
from datetime import datetime

def mmdd_to_dt(mmdd: str, year: int) -> datetime:
    return datetime.strptime(f"{year}/{mmdd}", "%Y/%m/%d")

def is_valid_mmdd(s: str) -> bool:
    if len(s) != 5 or s[2] != '/': return False
    mm, dd = s[:2], s[3:]
    return mm.isdigit() and dd.isdigit()

def is_valid_time_hhmm(s: str) -> bool:
    if len(s) != 5 or s[2] != ':': return False
    hh, mm = s[:2], s[3:]
    if not (hh.isdigit() and mm.isdigit()): return False
    h, m = int(hh), int(mm)
    return 0 <= h <= 23 and 0 <= m <= 59

def hex_to_rgb(hexcode: str):
    hexcode = hexcode.lstrip("#")
    return tuple(int(hexcode[i:i+2], 16) for i in (0,2,4))
