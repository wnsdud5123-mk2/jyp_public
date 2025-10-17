import tkinter as tk
from tkinter.ttk import Style as TkStyle
try:
    from ttkbootstrap import Style as BSStyle
except Exception:
    BSStyle = None

from .styles import PALETTE_DEFAULT

def init_ui(default_root: tk.Misc):
    # ttk가 _default_root를 참조하는 환경 보호
    import tkinter as _tk
    _tk._default_root = default_root

    # 기본 스타일 인스턴스
    TkStyle()
    if BSStyle:
        BSStyle()

    # 기본 팔레트 1회 적용(원치 않으면 주석)
    try:
        default_root.winfo_toplevel().tk_setPalette(**PALETTE_DEFAULT)
    except Exception:
        pass

class BaseWindow(tk.Toplevel):
    """NoDefaultRoot 환경에서 안전한 Toplevel 베이스"""
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        init_ui(self)
