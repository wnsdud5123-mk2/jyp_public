from __future__ import annotations
from datetime import date, datetime
import tkinter as tk

def _ensure_default_root(parent: tk.Misc):
    try:
        import tkinter as _tk
        _tk._support_default_root = True
        _tk._default_root = parent.winfo_toplevel()
    except Exception:
        pass

def _as_date(x):
    try:
        return x.date() if hasattr(x, "date") else x
    except Exception:
        return x

def _pick_with_tkcalendar(parent: tk.Misc, title: str, initial: date | None) -> date | None:
    """한 번 클릭하면 바로 확정되는 tkcalendar 모달."""
    try:
        from tkcalendar import Calendar
    except Exception:
        return None

    win = tk.Toplevel(parent)
    win.title(title)
    win.transient(parent)
    win.grab_set()

    cal = Calendar(win, selectmode="day", date_pattern="yyyy-mm-dd")
    cal.pack(padx=8, pady=8)

    if initial:
        try:
            cal.selection_set(_as_date(initial))
        except Exception:
            pass

    picked: dict[str, date | None] = {"d": None}

    def on_pick(_evt=None):
        try:
            picked["d"] = datetime.strptime(cal.get_date(), "%Y-%m-%d").date()
        except Exception:
            picked["d"] = None
        win.destroy()

    # 날짜 한 번 클릭하면 즉시 확정
    cal.bind("<<CalendarSelected>>", on_pick)

    # 버튼도 덤으로
    btn = tk.Button(win, text="확인", width=8, command=on_pick)
    btn.pack(pady=(0,8))

    win.wait_window()
    return picked["d"]

def _pick_single(parent: tk.Misc, title: str, initial: date | None) -> date | None:
    """우선 ttkbootstrap DatePickerDialog 시도 → 실패/미확정이면 tkcalendar 폴백."""
    _ensure_default_root(parent)

    # 1) ttkbootstrap 우선
    try:
        from ttkbootstrap.dialogs import DatePickerDialog
        d0 = _as_date(initial) or date.today()
        dlg = DatePickerDialog(parent=parent, title=title, firstweekday=6, startdate=d0)

        show = getattr(dlg, "show", None)
        if callable(show):
            r = show()
            if isinstance(r, date):
                return r

        # 모달 대기 후 확정값만 확인 (date는 초기값일 수 있으니 쓰지 않음)
        try:
            dlg.wait_window()
        except Exception:
            try:
                parent.wait_window(dlg)
            except Exception:
                pass

        for attr in ("result", "selected_date"):
            v = getattr(dlg, attr, None)
            if isinstance(v, date):
                return v

        # 여기까지 오면 미확정(그냥 닫힘)
    except Exception:
        # ttkbootstrap 자체가 실패한 경우
        pass

    # 2) 폴백: tkcalendar — 클릭 즉시 확정
    return _pick_with_tkcalendar(parent, title, initial)

def pick_date_range(parent, start: date | None = None, end: date | None = None, **_):
    s = _pick_single(parent, "시작일 선택", start)
    if not s:
        return None
    e = _pick_single(parent, "종료일 선택", end or s)
    if not e:
        return None
    return (s, e) if s <= e else (e, s)

def pick_single_date(parent, initial: date | None = None, **_):
    return _pick_single(parent, "날짜 선택", initial)
