# specials.py
import os
import re
import sys
VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
if os.path.isdir(VENDOR_DIR) and VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)
from pathlib import Path
from datetime import datetime, timedelta
import tkinter as tk
from datetime import date
from .ui.styles import DEFAULT_THEME as 기본테마
from .ui.datepickers import pick_date_range as _pick_range
from .ui.styles import DEFAULT_THEME as _APP_THEME
from .ui.styles import setup_styles, apply_theme_colors
from tkinter import ttk, messagebox, simpledialog, filedialog
import traceback
_HAVE_RANGE_PICKER = True  # 실제 임포트는 pick_date_range() 안에서 함
def _show_exc(self, exc, val, tb):
    msg = "".join(traceback.format_exception(exc, val, tb))
    try:
        # NoDefaultRoot 환경에서도 안전하게: parent=self
        messagebox.showerror("특가모음 오류", msg, parent=self)
    except Exception:
        # 그래도 실패하면 콘솔에 출력
        print("[SPECIALS ERROR]", msg)

# Tk가 콜백 예외를 이 함수로 넘기도록 설정 (self를 넘겨줍니다)
tk.Tk.report_callback_exception = _show_exc
tk.Toplevel.report_callback_exception = _show_exc
# tkcalendar(optional)
_HAS_TKCAL = True
try:
    from tkcalendar import Calendar
except Exception:
    _HAS_TKCAL = False

def _bind_default_root(widget: tk.Misc):
    """NoDefaultRoot 환경에서 ttk/ttkbootstrap이 참조할 default_root를 강제로 이 창으로 묶는다."""
    import tkinter as _tk
    try:
        _tk._support_default_root = True     # default root 사용 허용
        _tk._default_root = widget           # 이 창을 default_root로 지정
    except Exception:
        pass

# ── 경로 설정 ────────────────────────────────────────────────────────────
# config.py에 SPECIALS_DIR 가 있으면 그것을 우선 사용
DEFAULT_SPECIALS_DIR = r"\\10.2.0.113\홍보마케팅\_개인폴더_\이준영\터치X\특가"
try:
    from config import SPECIALS_DIR as _CFG_DIR  # type: ignore
    SPECIALS_DIR = Path(_CFG_DIR)
except Exception:
    SPECIALS_DIR = Path(DEFAULT_SPECIALS_DIR)

SPECIALS_DIR.mkdir(parents=True, exist_ok=True)

# ── 유틸: 한국식 날짜 포맷 ───────────────────────────────────────────────
def ymd(dt: datetime) -> str:
    return f"{dt.year:04d}/{dt.month:02d}/{dt.day:02d}"

def mmdd(dt: datetime) -> str:
    return f"{dt.month}/{dt.day:02d}"

# 파일명 → (start,end,type) 파싱
_DATE_FULL = re.compile(r"(\d{4})년(\d{1,2})월(\d{1,2})일")
_DATE_MD   = re.compile(r"(\d{1,2})월(\d{1,2})일")
_DATE_D    = re.compile(r"(\d{1,2})일")
_TYPE_RE   = re.compile(r"((?:밴드|여행사|문자)|[가-힣A-Za-z0-9_]+)\s*특가")

def parse_filename(fname: str):
    """
    예: '2025년09월29일30일 10월01일02일03일 여행사특가.txt'
    → (start_date, end_date, '여행사')
    파싱 실패 시 None 리턴
    """
    stem = Path(fname).stem  # 확장자 제거
    # 타입
    mtype = _TYPE_RE.search(stem)
    typ = mtype.group(1) if mtype else None

    # 날짜 토큰 전개
    dates = []
    pos = 0
    year_ctx = None
    month_ctx = None

    # 전체에서 왼→오 스캔
    while pos < len(stem):
        m = _DATE_FULL.search(stem, pos)
        md = _DATE_MD.search(stem, pos)
        d  = _DATE_D.search(stem, pos)

        # 가장 가까운 매치를 고름
        candidates = [(m, 'YMD'), (md, 'MD'), (d, 'D')]
        candidates = [(mx, kind) for mx, kind in candidates if mx]
        if not candidates:
            break
        mx, kind = min(candidates, key=lambda t: t[0].start())

        if kind == 'YMD':
            y, mo, da = map(int, mx.groups())
            year_ctx, month_ctx = y, mo
            dates.append(datetime(y, mo, da))
        elif kind == 'MD':
            mo, da = map(int, mx.groups())
            month_ctx = mo
            if year_ctx is None:
                # 연도가 처음 안 나왔다면 파일 수정시각의 연도 추정
                year_ctx = datetime.now().year
            dates.append(datetime(year_ctx, month_ctx, da))
        else:  # 'D'
            da = int(mx.group(1))
            if year_ctx is None or month_ctx is None:
                # 문법상 최소 한 번은 YMD/MD가 앞에 있었을 것
                year_ctx = datetime.now().year
                month_ctx = datetime.now().month
            dates.append(datetime(year_ctx, month_ctx, da))

        pos = mx.end()

    if not dates:
        return None
    dates.sort()
    start, end = dates[0], dates[-1]
    return start, end, typ

def build_filename_for_range(start: datetime, end: datetime, typ: str) -> str:
    """
    날짜 범위를 월 단위로 압축해서 예시 규칙으로 파일명 생성.
    첫 그룹만 'YYYY년MM월', 이후 그룹은 'MM월'만 표기.
    일은 2자리로 모아쓰기: 29일30일, 01일02일...
    """
    parts = []
    cur = start
    groups = []
    while cur <= end:
        groups.append(cur)
        cur += timedelta(days=1)

    # (year,month)별 그룹핑
    grouped = {}
    for dt in groups:
        grouped.setdefault((dt.year, dt.month), []).append(dt.day)

    for i, ((y, m), days) in enumerate(sorted(grouped.items())):
        day_str = "".join(f"{d:02d}일" for d in days)
        if i == 0:
            parts.append(f"{y}년{m:02d}월{day_str}")
        else:
            parts.append(f"{m:02d}월{day_str}")

    return " ".join(parts) + f" {typ}특가.txt"

def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="utf-8-sig")
        except Exception:
            try:
                return path.read_text(encoding="cp949")
            except Exception as e:
                return f"[읽기 오류] {e}"

def safe_write_text(path: Path, text: str):
    path.write_text(text, encoding="utf-8-sig")

# ── UI ──────────────────────────────────────────────────────────────────
# (필요하면 파일 상단에)
# from jyp.config import 기본테마  # 이게 접근 가능하다면 추천
# 없다면 아래 _apply_palette_basic에서 self의 현재 배경색을 써도 OK

class SpecialsWindow(tk.Toplevel):
    """특가 목록/본문 + 날짜범위/키워드 필터 UI"""

    def _apply_palette_basic(self):
        """달력 닫힌 뒤 앱 팔레트를 항상 원래 색으로 되돌린다."""
        top = self.winfo_toplevel()  # root 대체
        try:
            # 기본테마를 쓴다면:
            top.tk_setPalette(
                background=기본테마["배경"],
                foreground=기본테마["라벨글자"],
                activeBackground=기본테마["배경"],
                activeForeground=기본테마["라벨글자"],
                highlightColor=기본테마["배경"],
                selectBackground=기본테마["입력창배경"],
                selectForeground=기본테마["라벨글자"],
            )
        except Exception:
            # 기본테마가 이 모듈에서 접근 불가하면 현재 배경을 사용한 안전한 기본값
            bg = top.cget("bg")
            try:
                top.tk_setPalette(
                    background=bg, foreground="#000000",
                    activeBackground=bg, activeForeground="#000000",
                    highlightColor=bg, selectBackground="#e6e6e6",
                    selectForeground="#000000",
                )
            except Exception:
                pass

    # 날짜범위 선택(범위 캘린더 or 문자열 입력)
    def pick_date_range(self):
        cal_theme = {
            "background": "#ffffff", "foreground": "#000000",
            "activeBackground": "#ffffff", "activeForeground": "#000000",
            "highlightColor": "#ffffff", "selectBackground": "#e6e6e6",
            "selectForeground": "#000000",
        }
        restore_theme = {
            "background": 기본테마["배경"], "foreground": 기본테마["라벨글자"],
            "activeBackground": 기본테마["배경"], "activeForeground": 기본테마["라벨글자"],
            "highlightColor": 기본테마["배경"],
            "selectBackground": 기본테마["입력창배경"],
            "selectForeground": 기본테마["라벨글자"],
        }
        
        # 달력(임시 팔레트 적용)
        res = _pick_range(
            parent=self,
            start=self.range_from, end=self.range_to,
            calendar_theme=cal_theme,
            restore_theme=restore_theme,
        )
        print("[SW] pick_date_range ->", res)
    # 닫힌 직후, 앱/이 창 모두 재도색(팔레트가 전역이어서 확실히 원복)
        try:
            apply_theme_colors(self.master, 기본테마); setup_styles(self.master, 기본테마)
            apply_theme_colors(self, 기본테마);       setup_styles(self, 기본테마)
        except Exception:
            pass

        if not res:
            return
        d1, d2 = res
        if d1 > d2: d1, d2 = d2, d1
        self.range_from, self.range_to = d1, d2
        self.range_text.set(f"{d1:%Y-%m-%d}  –  {d2:%Y-%m-%d}")
        self.apply_filter()


    def __init__(self, master=None, side_list_on_left: bool = True):
        super().__init__(master)

        # ★ 핵심: 이 창을 default_root로 고정
        _bind_default_root(self)

        # ★ ttk / ttkbootstrap 스타일을 '반드시' 부모 지정해서 먼저 만든다
        from tkinter.ttk import Style as TkStyle
        TkStyle(master=self)

        try:
            from ttkbootstrap import Style as BSStyle
            self._bs_style = BSStyle(master=self)   # themename 지정 필요하면 여기서
        except Exception:
            self._bs_style = None

        self.title("특가모음")
        self.geometry("1000x620+80+60")
        self.minsize(900, 550)

        self.side_list_on_left = side_list_on_left
        self.items: list[dict] = []       # 전체 원본
        self.view_items: list[dict] = []  # 필터링된 목록(리스트박스에 표시)

        # 날짜 범위 상태
        self.range_text = tk.StringVar(master=self, value="")
        self.range_from: date | None = None
        self.range_to:   date | None = None

        # ── 상단 바
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)

        self.btn_cal = ttk.Button(top, text="📅 캘린더",
                                  command=self.pick_date_range, width=10)
        self.btn_cal.pack(side="left")

        self.ent_range = ttk.Entry(top, textvariable=self.range_text,
                                   width=24, state="readonly")
        self.ent_range.pack(side="left", padx=6)

        self.ent_kw = ttk.Entry(top, width=35)
        self.ent_kw.pack(side="left", padx=6)
        self.ent_kw.bind("<Return>", lambda e: self.apply_filter())

        self.btn_find = ttk.Button(top, text="찾기", command=self.apply_filter)
        self.btn_find.pack(side="left")

        ttk.Label(top, text=" ").pack(side="left", padx=6)  # spacer

        self.btn_add = ttk.Button(top, text="추가", command=self.open_add_window)
        self.btn_del = ttk.Button(top, text="삭제", command=self.delete_selected)
        self.btn_edit = ttk.Button(top, text="수정", command=self.start_edit)
        self.btn_confirm = ttk.Button(top, text="확인", command=self.commit_edit)
        self.btn_confirm.pack_forget()

        for b in (self.btn_add, self.btn_del, self.btn_edit):
            b.pack(side="left", padx=3)

        # ── 메인 패널
        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=6)

        # 목록
        left_frame = ttk.Frame(body)
        self.listbox = tk.Listbox(left_frame, activestyle="dotbox")
        self.listbox.pack(side="left", fill="both", expand=True)
        sb1 = ttk.Scrollbar(left_frame, command=self.listbox.yview)
        sb1.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=sb1.set)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        # 내용
        right_frame = ttk.Frame(body)
        self.txt = tk.Text(right_frame, wrap="word", state="disabled")
        self.txt.pack(side="left", fill="both", expand=True)
        sb2 = ttk.Scrollbar(right_frame, command=self.txt.yview)
        sb2.pack(side="right", fill="y")
        self.txt.config(yscrollcommand=sb2.set)

        if self.side_list_on_left:
            body.add(left_frame, weight=1)
            body.add(right_frame, weight=3)
        else:
            body.add(right_frame, weight=3)
            body.add(left_frame, weight=1)

        self.refresh_list()
        print("[SPECIALS CHILDREN]", self.winfo_children())
    # ── 데이터 로드 & 표시
    def load_all(self) -> list[dict]:
        entries: list[dict] = []
        for p in sorted(SPECIALS_DIR.glob("*.txt"), key=lambda x: x.name):
            parsed = parse_filename(p.name)
            if parsed:
                start, end, typ = parsed
                type_part = (typ + " " if typ else "")
                label = f"{start.month}월 {type_part}특가 {mmdd(start)}~{mmdd(end)}".strip()
            else:
                start = end = None
                typ = None
                label = p.stem
            entries.append({"path": p, "label": label, "start": start, "end": end, "type": typ})
        # 최신(끝나는 날짜) 먼저
        entries.sort(key=lambda it: (it["end"] or datetime.min), reverse=True)
        return entries

    def refresh_list(self):
        self.items = self.load_all()
        self.apply_filter()

    def _overlap(self, it: dict, d1: date, d2: date) -> bool:
        """it가 d1~d2와 겹치면 True (start/end가 None이면 통과)"""
        s, e = it.get("start"), it.get("end")
        if s and e:
            s = s.date() if hasattr(s, "date") else s
            e = e.date() if hasattr(e, "date") else e
            return not (e < d1 or s > d2)
        return True

    def apply_filter(self):
        kw = self.ent_kw.get().strip()
        d1, d2 = self.range_from, self.range_to

        data = self.items
        if kw:
            def _match(it: dict) -> bool:
                if kw in it["label"]:
                    return True
                # 본문까지 검색하려면 아래 한 줄의 주석을 해제
                # return kw in safe_read_text(it["path"])
                return False
            data = [it for it in data if _match(it)]

        if d1 and d2:
            data = [it for it in data if self._overlap(it, d1, d2)]

        # 렌더
        self.view_items = data
        self.listbox.delete(0, "end")
        for it in data:
            self.listbox.insert("end", it["label"])

        # 내용 영역 리셋
        self.txt.config(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.config(state="disabled")

    def current_item(self) -> dict | None:
        sel = self.listbox.curselection()
        if not sel:
            return None
        idx = sel[0]
        if 0 <= idx < len(self.view_items):
            return self.view_items[idx]
        return None

    def on_select(self, _evt=None):
        it = self.current_item()
        if not it:
            return
        text = safe_read_text(it["path"])
        self.txt.config(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", text)
        self.txt.config(state="disabled")

    # ── (구) 단일 날짜 선택: 필요 없으면 버튼 연결만 안 쓰면 됨
    def pick_date(self):
        if _HAS_TKCAL:
            win = tk.Toplevel(self)
            win.title("날짜 선택")
            cal = Calendar(win, selectmode="day", date_pattern="yyyy-mm-dd")
            cal.pack(padx=8, pady=8)
            def done():
                s = cal.get_date()
                _ = datetime.strptime(s, "%Y-%m-%d")  # 예전 로직 유지
                win.destroy()
                self.apply_filter()
            ttk.Button(win, text="확인", command=done).pack(pady=6)
        else:
            s = simpledialog.askstring("날짜 입력", "YYYY-MM-DD 형식으로 입력")
            if s:
                try:
                    _ = datetime.strptime(s, "%Y-%m-%d")
                    self.apply_filter()
                except Exception:
                    messagebox.showerror("형식 오류", "YYYY-MM-DD 형식으로 입력해주세요.", parent=self)

    # ── CRUD
    def open_add_window(self):
        AddSpecialWindow(self, on_created=self.refresh_list)

    def delete_selected(self):
        it = self.current_item()
        if not it:
            messagebox.showinfo("삭제", "선택된 특가가 없습니다.", parent=self)
            return
        if not messagebox.askyesno("삭제 확인", "정말 삭제합니까?", parent=self):
            return
        try:
            it["path"].unlink(missing_ok=True)
            self.refresh_list()
            self.txt.config(state="normal")
            self.txt.delete("1.0", "end")
            self.txt.config(state="disabled")
        except Exception as e:
            messagebox.showerror("삭제 실패", str(e), parent=self)

    def start_edit(self):
        it = self.current_item()
        if not it:
            messagebox.showinfo("수정", "선택된 특가가 없습니다.", parent=self)
            return
        self.txt.config(state="normal")
        self.btn_confirm.pack(side="left", padx=3)

    def commit_edit(self):
        it = self.current_item()
        if not it:
            return
        content = self.txt.get("1.0", "end-1c")
        try:
            safe_write_text(it["path"], content)
            self.txt.config(state="disabled")
            self.btn_confirm.pack_forget()
            messagebox.showinfo("완료", "수정 내용을 저장했습니다.", parent=self)
        except Exception as e:
            messagebox.showerror("저장 실패", str(e), parent=self)


class AddSpecialWindow(tk.Toplevel):
    def __init__(self, master, on_created=None):
        super().__init__(master)

        # ★ 핵심: 이 창을 default_root로 고정
        _bind_default_root(self)

        # ★ ttk / ttkbootstrap 스타일을 '반드시' 부모 지정해서 먼저 만든다
        from tkinter.ttk import Style as TkStyle
        TkStyle(master=self)

        try:
            from ttkbootstrap import Style as BSStyle
            self._bs_style = BSStyle(master=self)   # themename 지정 필요하면 여기서
        except Exception:
            self._bs_style = None

        self.title("특가 추가")
        self.geometry("820x560+120+80")
        self.on_created = on_created

        self.start: datetime | None = None
        self.end:   datetime | None = None
        self.typ = tk.StringVar(self, value="밴드")
        self.typ_custom = tk.StringVar(self, value="")

        # 상단: 날짜 라벨 + 버튼
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        ttk.Label(top, text="날짜:").pack(side="left")
        self.lbl_range = ttk.Label(top, text="(미선택)")
        self.lbl_range.pack(side="left", padx=6)
        ttk.Button(top, text="📅 날짜 선택", command=self.pick_range).pack(side="left", padx=6)

        # 하단: 생성
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=8, pady=8)
        ttk.Button(bottom, text="확인 및 생성", command=self.create_file).pack(side="right")

        # 본문 + 우측 구분
        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=6)

        # 본문
        left = ttk.Frame(body)
        ttk.Label(left, text="특가 내용 (Ctrl+V 붙여넣기)").pack(anchor="w")
        self.txt = tk.Text(left, wrap="word")
        self.txt.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(left, command=self.txt.yview)
        self.txt.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        body.add(left, weight=3)

        # 우측 구분
        right = ttk.LabelFrame(body, text="특가 구분")
        for name in ("밴드", "여행사", "문자"):
            ttk.Radiobutton(right, text=name, value=name, variable=self.typ,
                            command=lambda: self.typ_custom.set("")).pack(anchor="w", padx=6, pady=2)
        ttk.Label(right, text="직접입력").pack(anchor="w", padx=6, pady=(8, 2))
        ent = ttk.Entry(right, textvariable=self.typ_custom)
        ent.pack(fill="x", padx=6)
        body.add(right, weight=1)


    def pick_range(self):
        from datetime import datetime
        cal_theme = {
            "background": "#ffffff", "foreground": "#000000",
            "activeBackground": "#ffffff", "activeForeground": "#000000",
            "highlightColor": "#ffffff", "selectBackground": "#e6e6e6",
            "selectForeground": "#000000",
        }
        restore_theme = {
            "background": 기본테마["배경"], "foreground": 기본테마["라벨글자"],
            "activeBackground": 기본테마["배경"], "activeForeground": 기본테마["라벨글자"],
            "highlightColor": 기본테마["배경"],
            "selectBackground": 기본테마["입력창배경"],
            "selectForeground": 기본테마["라벨글자"],
        }

        res = _pick_range(
            parent=self,
            start=(self.start.date() if self.start else None),
            end=(self.end.date() if self.end else None),
            calendar_theme=cal_theme,
            restore_theme=restore_theme,
        )
        print("[ADD] pick_range ->", res)
        # 닫힌 직후 재도색
        try:
            apply_theme_colors(self.master, 기본테마); setup_styles(self.master, 기본테마)
            apply_theme_colors(self, 기본테마);       setup_styles(self, 기본테마)
        except Exception:
            pass

        if not res:
            return
        d1, d2 = res
        if d1 > d2: d1, d2 = d2, d1
        self.start = datetime.combine(d1, datetime.min.time())
        self.end   = datetime.combine(d2, datetime.min.time())
        self.lbl_range.config(text=f"{ymd(self.start)} ~ {ymd(self.end)}")

    def create_file(self):
        if not self.start or not self.end:
            messagebox.showinfo("안내", "날짜 범위를 먼저 선택하세요.", parent=self)
            return
        typ = (self.typ_custom.get().strip() or self.typ.get().strip())
        if not typ:
            messagebox.showinfo("안내", "특가 구분을 선택/입력하세요.", parent=self)
            return
        content = self.txt.get("1.0", "end-1c").rstrip()
        if not content:
            if not messagebox.askyesno("내용 없음", "본문이 비어있습니다. 그래도 생성할까요?", parent=self):
                return

        fname = build_filename_for_range(self.start, self.end, typ)
        path = SPECIALS_DIR / fname
        if path.exists():
            if not messagebox.askyesno("중복 확인", "동일한 이름의 파일이 있습니다. 덮어쓸까요?", parent=self):
                return
        try:
            safe_write_text(path, content)
            messagebox.showinfo("완료", f"생성됨:\n{path}", parent=self)
            self.destroy()
            if self.on_created:
                self.on_created()
        except Exception as e:
            messagebox.showerror("실패", str(e), parent=self)
