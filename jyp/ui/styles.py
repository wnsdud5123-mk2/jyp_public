# jyp/ui/styles.py

from tkinter import ttk

DEFAULT_THEME = {
    "배경": "#f5f8ef",
    "라벨글자": "#000000",
    "입력창배경": "#ffffff",
    "출력창배경": "#ffffff",
}
PALETTE = {}  # 필요 시 색 정의

# 현재 팔레트 저장용(복구)
_prev_palette = None

def _tk_set_palette(root, theme):
    bg = theme.get("배경")
    fg = theme.get("라벨글자")
    selbg = theme.get("입력창배경", bg)
    try:
        root.tk_setPalette(
            background=bg,
            foreground=fg,
            activeBackground=bg,
            activeForeground=fg,
            highlightColor=bg,
            selectBackground=selbg,
            selectForeground=fg,
        )
    except Exception:
        pass

def setup_styles(root, theme=DEFAULT_THEME):
    """Tk/ttk 공통 스타일을 root 기준으로 세팅."""
    _tk_set_palette(root, theme)

    try:
        style = ttk.Style(master=root)   # 🔴 master 꼭 지정
        # 기본 위젯들
        style.configure("TFrame",  background=theme["배경"])
        style.configure("TLabelframe", background=theme["배경"])
        style.configure("TLabelframe.Label", background=theme["배경"], foreground=theme["라벨글자"])
        style.configure("TLabel",  background=theme["배경"], foreground=theme["라벨글자"])
        style.configure("TButton", padding=4)
        style.configure("TScrollbar", gripcount=0)
        style.configure("TEntry",  fieldbackground=theme["입력창배경"])
        style.map("TButton", foreground=[("disabled", theme["라벨글자"])])
    except Exception:
        pass

def apply_temp_calendar_theme(root):
    """달력 다이얼로그 띄우기 직전, 대비 좋은 팔레트로 잠깐 변경."""
    global _prev_palette
    try:
        # 이전 팔레트 덤프
        _prev_palette = {
            "bg": root.cget("bg"),
        }
    except Exception:
        _prev_palette = None

    # 달력 보기 좋게 임시 팔레트(밝은 바탕/짙은 글자)
    temp = {
        "배경": "#ffffff",
        "라벨글자": "#222222",
        "입력창배경": "#ffffff",
        "출력창배경": "#ffffff",
    }
    _tk_set_palette(root, temp)
    try:
        style = ttk.Style(master=root)
        style.configure("TFrame", background=temp["배경"])
        style.configure("TLabel", background=temp["배경"], foreground=temp["라벨글자"])
        style.configure("TEntry", fieldbackground=temp["입력창배경"])
    except Exception:
        pass

def restore_app_palette(root, theme=DEFAULT_THEME):
    """달력 닫힌 뒤 앱 테마를 원래대로 복구."""
    _tk_set_palette(root, theme)
    try:
        style = ttk.Style(master=root)
        style.configure("TFrame", background=theme["배경"])
        style.configure("TLabel", background=theme["배경"], foreground=theme["라벨글자"])
        style.configure("TEntry", fieldbackground=theme["입력창배경"])
    except Exception:
        pass
# jyp/ui/styles.py 내부에 추가
def apply_theme_colors(root, theme=DEFAULT_THEME):
    """
    Tk 위젯들의 배경/전경색을 현재 테마에 맞춰 일괄 적용.
    ttk는 setup_styles()가 처리하므로, 여기서는 Tk 위젯 위주로 안전하게 시도.
    """
    _tk_set_palette(root, theme)

    def _paint(w):
        try:
            cls = w.winfo_class()
        except Exception:
            cls = ""

        bg = theme.get("배경", "#ffffff")
        fg = theme.get("라벨글자", "#000000")
        entrybg = theme.get("입력창배경", bg)
        outbg = theme.get("출력창배경", bg)

        # Tk 기본 위젯만 조심스럽게 적용
        try:
            if cls in ("Frame", "TFrame", "LabelFrame"):
                w.configure(bg=bg)
            elif cls == "Label":
                w.configure(bg=bg, fg=fg)
            elif cls == "Entry":
                w.configure(bg=entrybg, fg=fg, insertbackground=fg)
            elif cls == "Text":
                w.configure(bg=outbg, fg=fg, insertbackground=fg)
            elif cls == "Listbox":
                w.configure(bg=outbg, fg=fg)
            elif cls == "Canvas":
                # 캔버스는 배경만
                w.configure(bg=outbg)
            elif cls in ("Button", "Radiobutton", "Checkbutton"):
                w.configure(bg=bg, fg=fg, activebackground=bg, activeforeground=fg)
        except Exception:
            pass

        for child in w.winfo_children():
            _paint(child)

    _paint(root)
