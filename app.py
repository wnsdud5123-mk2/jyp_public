from PIL import Image, ImageTk, ImageEnhance, ImageOps
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
import os
import platform
import sys
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(__file__)
import pyperclip
# ===== 금지목록: 네트워크 공유 폴더에서 불러오기/저장하기 =====
BAN_DIR = r"\\10.2.0.113\홍보마케팅\_개인폴더_\이준영\터치X"
BAN_FILE_NOCADDY = os.path.join(BAN_DIR, "노캐디 금지목록.txt")
BAN_FILE_FIVE    = os.path.join(BAN_DIR, "5인플레이 금지목록.txt")

# 처음 가동 시 파일이 비어 있거나 없을 경우 사용할 기본값
_DEFAULT_NOCADDY = [
    "홍명열","최연홍","김청엽","이관승","고민서","이명신"
]
_DEFAULT_FIVE = [
    "박선철","최경진","조국정","심남열","서영주","성구현","이남진","윤순정",
    "김정식","권동진","김동현","신인호","석봉환","박진석","김지성","최기수",
    "박우세","서문억","나영수","김진수","최성관","차준관","오기택","김환태",
    "주훈종","조경희","강용운","김정수","박근용","박정진","이제휴","이득희"
]
# 메모리 내 목록(집합으로 관리: 중복 자동 정리)
노캐디금지목록  = set(_DEFAULT_NOCADDY)
오인플금지목록  = set(_DEFAULT_FIVE)
def _ban__read_lines(path: str) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip()]
    except Exception:
        return []
def _ban__write_lines(path: str, names: set[str]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for name in sorted(names):
            f.write(name + "\n")
def _ban_reload_from_disk():
    """공유폴더에서 목록을 다시 불러와 메모리에 반영."""
    global 노캐디금지목록, 오인플금지목록
    n = _ban__read_lines(BAN_FILE_NOCADDY)
    f = _ban__read_lines(BAN_FILE_FIVE)
    if n: 노캐디금지목록 = set(n)
    if f: 오인플금지목록 = set(f)
def _ban_persist(kind: str):
    """kind='nocaddy' | 'five' 에 해당하는 파일로 저장."""
    if kind == "nocaddy":
        _ban__write_lines(BAN_FILE_NOCADDY, 노캐디금지목록)
    else:
        _ban__write_lines(BAN_FILE_FIVE, 오인플금지목록)
# 시작할 때 한 번 시도
_ban_reload_from_disk()
TEMPLATES = {
    "카카오 발송문자": {
        "fields":[
            ("예약자", "name"),
            ("테스트1", "test1"),
            ("테스트2", "test2"),
        ],
        "format":
            "[장수골프리조트 사전예약안내]\n"
            "예약자: {name}님\n"
            "예약날: {test1}\n"
            "예약시간: {test2}\n"
            "감사합니다."
    },
    "예약확정문자": {
        "fields":[
            ("예약자", "name"),
            ("예약일자", "날짜", "date"),
            ("코스", "코스"),
            ("시간", "시간", "time"),
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
}
# 요일표
요일표 = {"Mon": "월","Tue": "화","Wed": "수","Thu": "목","Fri": "금","Sat": "토","Sun": "일"}
is_2박3일 = False  # 출력 형식 상태
# 색상 테마
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
root = tk.Tk()
root.title("1박2일 예약문자 생성기")
root.configure(bg=기본테마["배경"])
# [NEW] 시작 크기(대략 1.3배)
root.geometry("1180x720")
# 우측 출력영역이 창 크기에 맞춰 늘어나도록
root.grid_columnconfigure(1, weight=1)   # Text가 있는 열
root.grid_rowconfigure(0, weight=1)      # Text가 있는 행
# [NEW] 확정 문구 포함 토글 (기본: 꺼짐)
confirm_mode = tk.BooleanVar(value=False)
# [NEW] 룸 수(2/4) 선택 변수 (기본=2)
rooms_var = tk.IntVar(value=2)
# [NEW] 팀 수(1/2/3/4+) 상태 (4는 '4팀이상' → 시간칸 1개만)
team_var = tk.IntVar(value=1)
# [NEW] 1~3팀일 땐 고정값(프록시), 4팀이상일 땐 입력칸 사용
team_fixed_var = tk.IntVar(value=1)  # 1/2/3 버튼용
TEAM_ENTRY = None  # 실제 '팀 수' Entry 위젯을 저장
TEAM_LABEL = None  # '팀 수' Label (보이기/숨기기용)
# [NEW] 시간칸 컨테이너: 프레임(F), 엔트리 리스트(T)
F = {}  # ex) F["day1.time"] = Frame
T = {"day1": [], "day2": [], "day3": []}
# [NEW] IntVar를 W["rooms"]처럼 쓰기 위한 간단 프록시
class _VarProxy:
    def __init__(self, var): self.var = var
    def get(self): return str(self.var.get())
# 입력창 프레임
input_frame = tk.Frame(root, bg=기본테마["배경"])
input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="n")
# [NEW] 최상단 팀 수 버튼 (1/2/3/4+)
team_bar = tk.Frame(input_frame, bg=기본테마["배경"])
team_bar.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,6))
def _set_team(n):
    team_var.set(n)
    req = 1 if n == 4 else n
    # 1) 시간칸 개수 조정
    _ensure_time_count("day1", req)
    _ensure_time_count("day2", req)
    if is_2박3일:
        _ensure_time_count("day3", req)
    else:
        _ensure_time_count("day3", 1)
    # 2) 팀 수 값/입력칸 제어
    if n in (1, 2, 3):
        team_fixed_var.set(n)
        # W["teams"]를 프록시로 덮어써서 get()이 "1/2/3"을 돌리게
        W["teams"] = _VarProxy(team_fixed_var)
        # '팀 수' 라벨/입력칸 숨김
        if TEAM_LABEL: TEAM_LABEL.grid_remove()
        if TEAM_ENTRY: TEAM_ENTRY.grid_remove()
    else:
        # 4팀이상: 실제 입력칸을 사용
        if TEAM_LABEL: TEAM_LABEL.grid()
        if TEAM_ENTRY: TEAM_ENTRY.grid()
        # 비어있으면 4로 채워주기
        try:
            if TEAM_ENTRY.get().strip() == "":
                TEAM_ENTRY.insert(0, "4")
        except Exception:
            pass
        W["teams"] = TEAM_ENTRY
tk.Button(team_bar, text="1팀",    command=lambda:_set_team(1)).pack(side="left")
tk.Button(team_bar, text="2팀",    command=lambda:_set_team(2)).pack(side="left")
tk.Button(team_bar, text="3팀",    command=lambda:_set_team(3)).pack(side="left")
tk.Button(team_bar, text="4팀이상", command=lambda:_set_team(4)).pack(side="left")
# [REPLACE] 우측 출력 캔버스(배경이미지 + 텍스트)
text_canvas = tk.Canvas(root, bg=기본테마["출력창배경"], highlightthickness=0)
text_canvas.grid(row=0, column=1, rowspan=20, padx=(10,0), pady=10, sticky="nsew")
scrollbar = tk.Scrollbar(root, orient="vertical", command=text_canvas.yview)
scrollbar.grid(row=0, column=2, rowspan=20, sticky="ns", padx=(0,10), pady=10)
# [NEW] 처음 화면(런처)
home_frame = tk.Frame(root, bg=기본테마["배경"])
home_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")  # 처음엔 홈을 띄워둠
# 홈 화면 버튼들
tk.Label(home_frame, text="메인 메뉴", bg=기본테마["배경"], fg=기본테마["라벨글자"], font=("맑은 고딕", 16, "bold")).pack(pady=(20,12))
btn_pkg = tk.Button(home_frame, text="📦 패키지 문자", height=2, width=20, command=lambda: show_pkg())
btn_pkg.pack(pady=6)
# 금지목록 화면
ban_frame = tk.Frame(root, bg=기본테마["배경"])
ban_title = tk.Label(ban_frame, text="노캐디/5인플 금지 조회", bg=기본테마["배경"],
                     fg=기본테마["라벨글자"], font=("맑은 고딕", 14, "bold"))
ban_title.pack(pady=(20, 8))
PLACEHOLDER = "여기에 이름입력"   # ← 추가
# ↓ 기존 ban_input 생성·insert 부분 교체
ban_input = tk.Entry(ban_frame, width=28, bg=기본테마["입력창배경"], fg="#999")
ban_input.pack(pady=4)
ban_input.insert(0, PLACEHOLDER)
def _ban_ph_in(_=None):
    # 포커스 들어오면 placeholder면 지우고 진한 글씨로
    if ban_input.get() == PLACEHOLDER:
        ban_input.delete(0, tk.END)
        ban_input.config(fg="#000")
def _ban_ph_out(_=None):
    # 포커스 빠졌는데 비어 있으면 placeholder 복구
    if not ban_input.get().strip():
        ban_input.delete(0, tk.END)
        ban_input.insert(0, PLACEHOLDER)
        ban_input.config(fg="#999")
ban_input.bind("<FocusIn>", _ban_ph_in)
ban_input.bind("<FocusOut>", _ban_ph_out)
ban_input.bind("<Button-1>", _ban_ph_in, add="+")
# [NEW] 결과 라벨
ban_result = tk.Label(
    ban_frame,
    text="가능: 07:30 이후, 12:30 이후 가능",
    bg=기본테마["배경"],
    fg="#2e7d32"
)
ban_result.pack(pady=(6, 12))
# [NEW] 버튼들
ban_btn_row = tk.Frame(ban_frame, bg=기본테마["배경"])
ban_btn_row.pack(pady=4)
tk.Button(
    ban_btn_row, text="조회",
    command=lambda: _ban_check(ban_input, ban_result)
).pack(side="left", padx=6)
tk.Button(
    ban_btn_row, text="⬅ 처음으로",
    command=lambda: show_home()
).pack(side="left", padx=6)
tk.Button(
    ban_btn_row, text="📋 결과 복사",
    command=lambda: _ban_copy(ban_result)
).pack(side="left", padx=6)
# 엔터로도 조회
ban_input.bind("<Return>", lambda e: _ban_check(ban_input, ban_result))
# ===== 금지목록 편집 섹션 =====
ban_edit = tk.LabelFrame(ban_frame, text="금지목록 편집", bg=기본테마["배경"])
ban_edit.pack(pady=(8, 12), padx=10, fill="x")
tk.Label(ban_edit, text="이름", bg=기본테마["배경"]).grid(row=0, column=0, padx=(8,4), pady=6, sticky="e")
ban_edit_name = tk.Entry(ban_edit, width=18, bg=기본테마["입력창배경"])
ban_edit_name.grid(row=0, column=1, padx=(0,8), pady=6, sticky="w")
ban_kind = tk.StringVar(value="nocaddy")
tk.Radiobutton(ban_edit, text="노캐디",    variable=ban_kind, value="nocaddy", bg=기본테마["배경"])\
  .grid(row=0, column=2, padx=6, sticky="w")
tk.Radiobutton(ban_edit, text="5인플레이", variable=ban_kind, value="five",     bg=기본테마["배경"])\
  .grid(row=0, column=3, padx=6, sticky="w")
def _ban_add():
    name = ban_edit_name.get().strip()
    if not name:
        messagebox.showwarning("입력 필요", "추가할 이름을 입력하세요.")
        return
    s = 노캐디금지목록 if ban_kind.get()=="nocaddy" else 오인플금지목록
    if name in s:
        messagebox.showinfo("중복", f"이미 등록되어 있습니다: {name}")
        return
    s.add(name)
    _ban_persist(ban_kind.get())
    messagebox.showinfo("완료", f"추가 및 저장 완료: {name}")
    ban_edit_name.delete(0, tk.END)
def _ban_remove():
    name = ban_edit_name.get().strip()
    if not name:
        messagebox.showwarning("입력 필요", "삭제할 이름을 입력하세요.")
        return
    s = 노캐디금지목록 if ban_kind.get()=="nocaddy" else 오인플금지목록
    if name not in s:
        messagebox.showinfo("없음", f"목록에 없습니다: {name}")
        return
    s.remove(name)
    _ban_persist(ban_kind.get())
    messagebox.showinfo("완료", f"삭제 및 저장 완료: {name}")
    ban_edit_name.delete(0, tk.END)
def _ban_refresh():
    _ban_reload_from_disk()
    messagebox.showinfo("새로고침", "공유폴더에서 최신 목록을 다시 불러왔습니다.")
tk.Button(ban_edit, text="추가",   command=_ban_add).grid(  row=0, column=4, padx=4)
tk.Button(ban_edit, text="삭제",   command=_ban_remove).grid(row=0, column=5, padx=4)
tk.Button(ban_edit, text="새로고침", command=_ban_refresh).grid(row=0, column=6, padx=4)
#ban_input.bind("<Return>", lambda e: _ban_check(ban_input, ban_result))  # 엔터로 조회
# 다른 프로그램 버튼 자리(원하면 실제 함수 연결)
btn_ban = tk.Button(home_frame, text="🚫 금지목록", height=1, width=20, command=lambda: show_ban())
btn_ban.pack(pady=4)
btn_prog3 = tk.Button(home_frame, text="🧪 준비중", height=1, width=20, command=lambda: show_prep())
btn_prog3.pack(pady=4)
# ===== [NEW] 준비중(템플릿 문자) 화면 =====
prep_frame = tk.Frame(root, bg=기본테마["배경"])
# 3분할: 빨강(왼) / 초록(가운데) / 파랑(오른쪽)
prep_frame.grid_columnconfigure(0, weight=0)   # 빨강: 고정폭
prep_frame.grid_columnconfigure(1, weight=0)   # 초록: 내용폭
prep_frame.grid_columnconfigure(2, weight=1)   # 파랑: 넓게 확장
prep_frame.grid_rowconfigure(0, weight=1)
# --- 빨강: 꼬리표 찾기/선택 ---
prep_left = tk.Frame(prep_frame, bg=기본테마["배경"])
prep_left.grid(row=0, column=0, sticky="nsw", padx=(16,10), pady=16)

tk.Label(prep_left, text="꼬리표 찾기", bg=기본테마["배경"], fg=기본테마["라벨글자"],
         font=("맑은 고딕", 11, "bold")).pack(anchor="w")
prep_search = tk.Entry(prep_left, width=24, bg=기본테마["입력창배경"])
prep_search.pack(pady=(4,8), anchor="w")
prep_list = tk.Listbox(prep_left, height=20, width=24, exportselection=False)
prep_list.pack(fill="y")
# --- 초록: 동적 입력칸(폼) ---
prep_mid = tk.Frame(prep_frame, bg=기본테마["배경"])
prep_mid.grid(row=0, column=1, sticky="nsw", padx=(10,10), pady=16)
tk.Label(prep_mid, text="입력", bg=기본테마["배경"], fg=기본테마["라벨글자"],
         font=("맑은 고딕", 11, "bold")).grid(row=0, column=0, sticky="w")
prep_form = tk.Frame(prep_mid, bg=기본테마["배경"])
prep_form.grid(row=1, column=0, sticky="nw")
prep_btns = tk.Frame(prep_mid, bg=기본테마["배경"])
prep_btns.grid(row=2, column=0, sticky="w", pady=(8,0))
tk.Button(prep_btns, text="📋 복사", command=lambda: _prep_copy()).pack(side="left", padx=4)
tk.Button(prep_btns, text="✍ 직접수정", command=lambda: _prep_enable_edit()).pack(side="left", padx=4)
tk.Button(prep_btns, text="⬅ 처음으로", command=lambda: show_home()).pack(side="left", padx=4)
tk.Button(prep_btns, text="🖨 출력", command=lambda: _prep_render()).pack(side="left", padx=4)
# --- 파랑: 출력/수정 텍스트 ---
prep_right = tk.Frame(prep_frame, bg=기본테마["배경"])
prep_right.grid(row=0, column=2, sticky="nsew", padx=(10,16), pady=16)
prep_text = tk.Text(prep_right, wrap="word", bg=기본테마["출력창배경"], state="disabled")
prep_text.pack(fill="both", expand=True)
# 상태 보관
_prep_selected = tk.StringVar(value="")
_prep_fields = {}  # {키: Entry}
# 종료 버튼(선택)
tk.Button(home_frame, text="닫기", command=root.destroy).pack(pady=(20,10))
text_canvas.configure(yscrollcommand=scrollbar.set)
# 캔버스 아이템(배경, 텍스트)
_canvas_bg = text_canvas.create_image(0, 0, anchor="nw")  # 배경용
_canvas_text = text_canvas.create_text(
    8, 8, anchor="nw", text="", width=1  # width는 리사이즈 때 갱신
)
# 초기 한 번 폭/배경 갱신  ← 호출 시점에 함수가 정의되어 있도록 람다로 감싼다
root.after(0, lambda: _update_canvas_bg())
# 창/캔버스 크기 바뀔 때마다 폭/배경 갱신 (일반/씹덕 공통)
text_canvas.bind("<Configure>", lambda e: _update_canvas_bg(), add="+")
root.bind("<Configure>",       lambda e: _update_canvas_bg(), add="+")
_last_output = ""  # 복사용 최신 문자열
# [NEW] 출력창 직접수정용 임시 에디터(Text). 편집 중이 아닐 땐 None
edit_text = None
entry_widgets = []
labels_위젯들 = []
label_texts = [
    "예약자 이름", "첫 번째 날 (MM/DD)", "첫 번째 날 시간",
    "두 번째 날 시간", "세 번째 날 시간",
    "팀 수", "룸 수", "패키지 가격"
]
# [NEW] 이름 기반 위젯 레지스트리
W = {}   # entries by name
L = {}   # labels  by name
key_names = ["name","day1.date","day1.time","day2.time","day3.time","teams","rooms","price"]
def 자동입력(event, 구분):
    내용 = event.widget.get()
    if 구분 == "/":
        if len(내용) == 2 and '/' not in 내용:
            event.widget.insert(tk.END, '/')
    elif 구분 == ":":
        if len(내용) == 2 and ':' not in 내용:
            event.widget.insert(tk.END, ':')
    elif 구분 == ",":
        if 내용.replace(",", "").isdigit():
            포맷 = f"{int(내용.replace(',', '')):,}"
            event.widget.delete(0, tk.END)
            event.widget.insert(0, 포맷)
          # [NEW] 시간 엔트리 생성 헬퍼
def _make_time_entry(parent, top=False):
    e = tk.Entry(parent, bg=기본테마["입력창배경"], width=10)
    e.bind("<KeyRelease>", lambda ev, 구분=":": 자동입력(ev, 구분))
    # 첫 번째 칸이면 위쪽 여백 0, 이후 칸은 위 2px 정도
    e.pack(anchor="w", pady=(0, 2) if top else (2, 2))
    return e
for i, text in enumerate(label_texts):
    label = tk.Label(input_frame, text=text, bg=기본테마["배경"], fg=기본테마["라벨글자"])
    label.grid(row=i+1, column=0, sticky="w", pady=2)
    entry = tk.Entry(input_frame, bg=기본테마["입력창배경"])
    entry.grid(row=i+1, column=1, pady=2)
    # 룸 수: Entry → 라디오 2/4
    if text == "룸 수":
        entry.destroy()
        rooms_frame = tk.Frame(input_frame, bg=기본테마["배경"])
        rooms_frame.grid(row=i+1, column=1, pady=2, sticky="w")
        tk.Radiobutton(rooms_frame, text="2룸", variable=rooms_var, value=2, bg=기본테마["배경"]).pack(side="left")
        tk.Radiobutton(rooms_frame, text="4룸", variable=rooms_var, value=4, bg=기본테마["배경"]).pack(side="left")
        entry = rooms_frame  # 테마 토글용으로 Frame를 들고 있게 함
    # 시간: Frame + 첫 엔트리(e0)
    if "시간" in text:
        entry.destroy()
        cell = tk.Frame(input_frame, bg=기본테마["배경"])
        cell.grid(row=i+1, column=1, pady=(0, 2), sticky="w")
        if text.startswith("첫 번째"):
            day, key = "day1", "day1.time"
        elif text.startswith("두 번째"):
            day, key = "day2", "day2.time"
        else:
            day, key = "day3", "day3.time"
        e0 = _make_time_entry(cell, top=True)
        F[key] = cell
        T[day] = [e0]
        cell._first_entry = e0
        entry = cell
        # [NEW] 시간 라벨은 첫 입력칸과 수평이 되도록 상단 정렬 + 동일 여백
        label.grid_configure(sticky="nw", pady=(0, 2))
    elif "날" in text:
        entry.bind("<KeyRelease>", lambda e, 구분="/": 자동입력(e, 구분))
    elif "가격" in text:
        entry.bind("<KeyRelease>", lambda e, 구분=",": 자동입력(e, 구분))
    # [NEW] '팀 수' 라벨/엔트리 포인터 저장 (4팀이상에서 표시하기 위해)
    if text == "팀 수":
        TEAM_ENTRY = entry
        TEAM_LABEL = label
    # === 여기부터는 if/elif 바깥에서 "한 번만" 등록 ===
    labels_위젯들.append(label)
    entry_widgets.append(entry)
    key = key_names[i]         # 각 라벨에 매칭된 이름 키
    W[key] = entry             # 기본은 entry(Entry/Frame)
    L[key] = label
    # 시간칸이면 첫 엔트리를 W[key]로 매핑
    if "시간" in text and hasattr(entry, "_first_entry"):
        W[key] = entry._first_entry
    # 룸 수는 프록시로 값(2/4)을 반환하게 덮어쓰기
    if text == "룸 수":
        W["rooms"] = _VarProxy(rooms_var)
# 셋째날 관련 위젯 숨기기 함수
for k in ("day3.time",):
    if k in L:
        L[k].grid_remove()
    if k in F:
        F[k].grid_remove()  # Frame 자체를 숨김
# ===== 유틸: MM/DD를 연도 자동 보정해서 datetime으로 =====
def _mmdd_to_dt(mmdd: str, base_year: int) -> datetime:
    """'MM/DD'를 base_year로 파싱. 달/일 유효성 체크 포함."""
    try:
        return datetime.strptime(f"{base_year}/" + mmdd, "%Y/%m/%d")
    except ValueError:
        raise
def _is_valid_mmdd(s: str) -> bool:
    if len(s) != 5 or s[2] != '/':
        return False
    mm, dd = s[:2], s[3:]
    if not (mm.isdigit() and dd.isdigit()):
        return False
    m, d = int(mm), int(dd)
    return 1 <= m <= 12 and 1 <= d <= 31  # 세부 일수는 datetime 파싱에서 최종 검증
def _is_valid_time_hhmm(s: str) -> bool:
    if len(s) != 5 or s[2] != ':':
        return False
    hh, mm = s[:2], s[3:]
    if not (hh.isdigit() and mm.isdigit()):
        return False
    h, m = int(hh), int(mm)
    return 0 <= h <= 23 and 0 <= m <= 59
def resolve_dates_with_years(first_mmdd: str, second_mmdd: str, third_mmdd: str | None = None):
    """현재 연도를 기준으로 연말→연초 넘어감 자동 보정.
    d1: 올해, d2: d1보다 앞달/앞일이면 내년으로, d3도 d2 기준 동일 규칙.
    """
    year_now = datetime.now().year
    d1 = _mmdd_to_dt(first_mmdd, year_now)
    d2_try = _mmdd_to_dt(second_mmdd, d1.year)
    if (d2_try.month, d2_try.day) < (d1.month, d1.day):
        d2 = _mmdd_to_dt(second_mmdd, d1.year + 1)
    else:
        d2 = d2_try
    d3 = None
    if third_mmdd:
        d3_try = _mmdd_to_dt(third_mmdd, d2.year)
        if (d3_try.month, d3_try.day) < (d2.month, d2.day):
            d3 = _mmdd_to_dt(third_mmdd, d2.year + 1)
        else:
            d3 = d3_try
    return d1, d2, d3
  # [NEW] 팀/모드에 맞춰 시간칸 개수 조정
def _ensure_time_count(day: str, count: int):
    key = f"{day}.time"
    frame = F.get(key)
    if not frame:
        return
    lst = T[day]
    # 늘리기
    while len(lst) < count:
        lst.append(_make_time_entry(frame, top=False))
    # 줄이기
    while len(lst) > count:
        w = lst.pop()
        try: w.destroy()
        except: pass
# [NEW] HEX -> RGB
def _hex_to_rgb(hexcode: str):
    hexcode = hexcode.lstrip("#")
    return tuple(int(hexcode[i:i+2], 16) for i in (0, 2, 4))
# [REPLACE] Text 아래에 배경 라벨을 깔고 갱신하는 버전
def _update_canvas_bg():
    try:
        root.update_idletasks()
        w = text_canvas.winfo_width()
        h = text_canvas.winfo_height()
        if w <= 4 or h <= 4:
            return
        # ✅ 항상 줄바꿈 폭부터 맞춘다 (일반/씹덕 공통)
        text_canvas.itemconfigure(_canvas_text, width=w-16)
        text_canvas.configure(scrollregion=text_canvas.bbox("all"))
        # 일반모드면 배경 이미지는 지우고 끝
        if root.cget("bg") != 씹덕테마["배경"]:
            text_canvas.itemconfigure(_canvas_bg, image="")  # 배경 제거
            return
        # ↓↓↓ 아래는 기존 배경 크롭+안개 코드 그대로 유지 ↓↓↓
        base = getattr(root, "_bg_base", None)
        if base is None:
            base = Image.open(os.path.join(BASE_DIR, "hum.jpg")).convert("RGBA")
            base = base.resize((root.winfo_width(), root.winfo_height()))
            root._bg_base = base
        abs_x = text_canvas.winfo_rootx() - root.winfo_rootx()
        abs_y = text_canvas.winfo_rooty() - root.winfo_rooty()
        crop = base.crop((abs_x, abs_y, abs_x + w, abs_y + h))
        r, g, b = _hex_to_rgb(씹덕테마["출력창배경"])
        fog  = Image.new("RGBA", (w, h), (r, g, b, 170))
        comp = Image.alpha_composite(crop, fog)
        tkimg = ImageTk.PhotoImage(comp)
        text_canvas._bgimg = tkimg
        text_canvas.itemconfigure(_canvas_bg, image=tkimg)
        text_canvas.coords(_canvas_bg, 0, 0)
        # 스크롤 영역 재설정(한 번 더 안전하게)
        text_canvas.configure(scrollregion=text_canvas.bbox("all"))
    except Exception as e:
        print("canvas bg failed:", e)
# [NEW] 출력 캔버스 위에 임시 Text 에디터를 얹어 편집하기
def _sync_editor_geometry():
    """에디터(Text)를 출력 캔버스와 정확히 겹치게 배치"""
    if not edit_text:
        return
    root.update_idletasks()
    x, y = text_canvas.winfo_x(), text_canvas.winfo_y()
    w, h = text_canvas.winfo_width(), text_canvas.winfo_height()
    edit_text.place(in_=root, x=x, y=y, width=w, height=h)
    # 스크롤바를 에디터와 연결
    scrollbar.config(command=edit_text.yview)
    edit_text.config(yscrollcommand=scrollbar.set)
def _apply_editor():
    """에디터 내용 적용하고 닫기"""
    global edit_text, _last_output
    if not edit_text:
        return
    _last_output = edit_text.get("1.0", "end-1c")
    # 캔버스 텍스트 갱신
    text_canvas.itemconfigure(_canvas_text, text=_last_output)
    text_canvas.configure(scrollregion=text_canvas.bbox("all"))
    # 스크롤바를 다시 캔버스로 복원
    scrollbar.config(command=text_canvas.yview)
    text_canvas.configure(yscrollcommand=scrollbar.set)
    # 에디터 제거
    edit_text.place_forget()
    edit_text.destroy()
    edit_text = None
    # 전환/리사이즈 대응
    _update_canvas_bg()
def _cancel_editor():
    """에디터 닫기(변경 취소)"""
    global edit_text
    if not edit_text:
        return
    # 스크롤바 원복
    scrollbar.config(command=text_canvas.yview)
    text_canvas.configure(yscrollcommand=scrollbar.set)
    edit_text.place_forget()
    edit_text.destroy()
    edit_text = None
    _update_canvas_bg()
def _open_editor():
    """임시 에디터 열기. 이미 열려 있으면 포커스만"""
    global edit_text
    if edit_text:
        try: edit_text.focus_set()
        except: pass
        return
    # Text 생성 (배경은 현재 테마의 출력창 배경색과 맞춤)
    bg = 씹덕테마["출력창배경"] if root.cget("bg") == 씹덕테마["배경"] else 기본테마["출력창배경"]
    t = tk.Text(root, wrap="word", undo=True, bg=bg)
    # 현재 출력 텍스트를 로드
    current = text_canvas.itemcget(_canvas_text, "text") or _last_output
    t.insert("1.0", current)
    # 단축키: Ctrl+Enter = 적용, Esc = 취소
    t.bind("<Control-Return>", lambda e: (_apply_editor(), "break"))
    t.bind("<Escape>",         lambda e: (_cancel_editor(), "break"))
    # 마우스 스크롤 연동
    t.bind("<MouseWheel>", lambda e: (t.yview_scroll(-1 if e.delta>0 else 1, "units"), "break"))
    # 전역 보관 + 배치
    edit_text = t
    _sync_editor_geometry()
    t.focus_set()
    # 창/캔버스 리사이즈 때도 따라 움직이게
    root.bind("<Configure>", lambda e: _sync_editor_geometry(), add="+")
# [NEW] 초기 팀 상태 적용 (앱 시작 시 1팀으로 세팅: 입력칸 숨김)
_set_team(team_var.get())
# ===== 입력값 검증 =====
def validate_inputs(is_2박3일_mode: bool):
    errors = []
    예약자   = W["name"].get().strip()
    첫날     = W["day1.date"].get().strip()
    첫날시간 = W["day1.time"].get().strip()
    둘째날시간 = W["day2.time"].get().strip()
    셋째날시간 = W["day3.time"].get().strip()
      # [NEW] 팀 수에 따른 추가 시간칸 검증
    req = 1 if (team_var.get() == 4) else team_var.get()
    # day1/day2는 항상
    for s in [e.get().strip() for e in T["day1"][:req]]:
        if not _is_valid_time_hhmm(s): errors.append("첫 번째 날: HH:MM 형식 확인")
    for s in [e.get().strip() for e in T["day2"][:req]]:
        if not _is_valid_time_hhmm(s): errors.append("두 번째 날: HH:MM 형식 확인")
    # day3는 2박3일일 때만
    if is_2박3일:
        for s in [e.get().strip() for e in T["day3"][:req]]:
            if not _is_valid_time_hhmm(s): errors.append("세 번째 날: HH:MM 형식 확인")
    팀수     = W["teams"].get().strip()
    룸수     = W["rooms"].get().strip()
    가격     = W["price"].get().strip()
    # 팀/룸 정수
    if not 팀수.isdigit() or int(팀수) <= 0:
        errors.append("팀 수: 1 이상의 정수를 입력하세요.")
    if not 룸수.isdigit() or int(룸수) not in (2, 4):
        errors.append("룸 수: 2 또는 4만 선택하세요.")
    # 날짜 형식 MM/DD
    if not _is_valid_mmdd(첫날):
        errors.append("첫 번째 날: MM/DD 형식으로 입력하세요 (예: 08/15).")
    # 시간 형식 HH:MM (00-23 / 00-59)
    if not _is_valid_time_hhmm(첫날시간):
        errors.append("첫 번째 날 시간: HH:MM 24시간 형식으로 입력하세요 (예: 07:30).")
    if not _is_valid_time_hhmm(둘째날시간):
        errors.append("두 번째 날 시간: HH:MM 24시간 형식으로 입력하세요 (예: 07:30).")
    if is_2박3일_mode and not _is_valid_time_hhmm(셋째날시간):
        errors.append("세 번째 날 시간: HH:MM 24시간 형식으로 입력하세요 (예: 07:30).")
    # 날짜 유효성(2월 30일 등) 및 연도 보정까지 시도
    if not errors:
        try:
            _mmdd_to_dt(첫날, datetime.now().year)
        except ValueError as ve:
            errors.append(f"날짜가 올바르지 않습니다: {ve}")
    return errors
# 예약문구 출력 함수 (기존 문구/형식 유지)
def 예약확인():
    global _last_output
    try:
        # 2. 입력값 검증 (무엇이 문제인지 경고창)
        errs = validate_inputs(is_2박3일)
        if errs:
            messagebox.showerror("입력 오류", "\n".join(f"- {e}" for e in errs))
            return
        예약자   = W["name"].get()
        첫날     = W["day1.date"].get()
        첫날시간 = W["day1.time"].get()
        둘째날시간 = W["day2.time"].get()
        셋째날시간 = W["day3.time"].get()
        팀수     = int(W["teams"].get())  
              # [NEW] 팀 수에 맞춰 시간 문자열 합치기
        req = 1 if (team_var.get() == 4) else team_var.get()
        def _join(day):
            return ", ".join(e.get().strip() for e in T[day][:req])
        첫날시간들  = _join("day1")
        둘째날시간들 = _join("day2")
        셋째날시간들 = _join("day3") if is_2박3일 else ""
        header_tag = "예약확정 안내"
        팀라인 = f"{팀수}팀({팀수*4}명)예약 확정 되었습니다."
        # 확정 전용 문구는 더 이상 쓰지 않음
        룸수     = int(W["rooms"].get())
        가격     = W["price"].get()
        # 1. 연도 자동 처리 (연말→연초 보정)
        # 첫날 datetime
        d1 = _mmdd_to_dt(첫날, datetime.now().year)
        # 자동 계산
        d2 = d1 + timedelta(days=1)
        d3 = d1 + timedelta(days=2) if is_2박3일 else None
        # 출력용 MM/DD 문자열
        둘째날 = d2.strftime("%m/%d")
        셋째날 = d3.strftime("%m/%d") if is_2박3일 else ""
        # 요일
        요일1 = 요일표[d1.strftime("%a")]
        요일2 = 요일표[d2.strftime("%a")]
        if is_2박3일:
            요일3 = 요일표[d3.strftime("%a")]
            출력 = f"""[장수CC 2박3일 {header_tag}]
예약자: {예약자}님
■{첫날}({요일1}) {첫날시간들}
■{둘째날}({요일2}) {둘째날시간들}
■{셋째날}({요일3}) {셋째날시간들}
{팀라인}

[유의사항]
*본 예약은 확정되었으며,
*취소는 전화로만 가능하고,
자동취소는 되지 않습니다.
*2주전 취소부터는 위약발생
*티오프 최소 30분전 내장!!

[이용 요금]
*패키지(1인): {가격}원
(그린피3일(54홀)+숙박2일+조식2회포함)
※불포함:카트피,캐디피
※팀당 4인플레이 기준

[숙박안내]
*일자: {첫날}({요일1}), {둘째날}({요일2})
숙소: 장수스테이  {팀수}객실
{룸수}룸타입(방{룸수},욕실2,거실1)
★ 객실내 취사 및 흡연 불가

[조식안내]
*2일차 라운드전 클럽하우스
※라운드 시작이후 이용불가
※티오프 50분전부터 식사가능
※ 제공 시간은 9시까지  ※

[예약금]
*금 액: {팀수*30}만원 (팀당30만원)
*은 행:기업은행
*계 좌:232-112996-01-015
*예금주:장수레저(주)
※입금후 확인연락바랍니다.

상기예약은 확정되었습니다.
감사합니다.

-장수골프리조트"""
        else:
            출력 = f"""[장수CC 1박2일 {header_tag}]
예약자: {예약자}님
■{첫날}({요일1}) {첫날시간들}
■{둘째날}({요일2}) {둘째날시간들}
{팀라인}

[유의사항]
*본 예약은 확정되었으며,
*취소는 전화로만 가능하며,
자동취소는 되지 않습니다.
*2주전 취소부터는 위약발생
*티오프 최소 30분전 내장!!

[이용 요금]
*패키지(1인): {가격}원
(그린피2일(36홀)+숙박+조식포함)
※불포함:카트피,캐디피
※팀당 4인플레이 기준

[숙박안내]
*일자: {첫날}({요일1})
숙소: 장수스테이  {팀수}객실
{룸수}룸타입(방{룸수},욕실2,거실1)
★ 객실내 취사 및 흡연 불가

[조식안내]
*2일차 라운드전 클럽하우스
※라운드 시작이후 이용불가
※티오프 50분전부터 식사가능
※ 제공 시간은 9시까지  ※

[예약금]
*금 액: {팀수*30}만원 (팀당30만원)
*은 행:기업은행
*계 좌:232-112996-01-015
*예금주:장수레저(주)
※입금후 확인연락바랍니다.

상기예약은 확정되었습니다.
감사합니다.

-장수골프리조트"""

        # 씹덕테마면 배경(크롭+안개)을 먼저 깔고, 그 위에 출력 텍스트를 쓴다
        # 텍스트만 갱신 (배경은 별도 라벨이어서 그대로 유지됨)
        # 캔버스 텍스트 갱신
        text_canvas.itemconfigure(_canvas_text, text=출력)
        text_canvas.configure(scrollregion=text_canvas.bbox("all"))
        _last_output = 출력
        # 씹덕모드면 배경도 재크롭
        if root.cget("bg") == 씹덕테마["배경"]:
            _update_canvas_bg()
    except Exception as e:
        messagebox.showerror("에러", str(e))
# 버튼 정의
def 모드전환():
    global is_2박3일
    is_2박3일 = not is_2박3일
    label = "2박3일 예약문자 생성기" if is_2박3일 else "1박2일 예약문자 생성기"
    root.title(label)
    button_2박3일.config(text="1박2일 예약 전환" if is_2박3일 else "2박3일 예약 전환")
    # [FIX] day3는 라벨(L)과 프레임(F)만 토글한다. 엔트리(W)는 pack이므로 grid 금지
    req = 1 if team_var.get() == 4 else team_var.get()
    if is_2박3일:
        _ensure_time_count("day3", req)   # 먼저 개수 맞추고
        L["day3.time"].grid()             # 라벨 보이기
        F["day3.time"].grid()             # 프레임 보이기
    else:
        _ensure_time_count("day3", 1)     # 1박2일은 항상 1칸만
        if "day3.time" in L: L["day3.time"].grid_remove()
        if "day3.time" in F: F["day3.time"].grid_remove()
# 4. 복사 버튼: 복사 후 알림
def 결과복사():
    try:
        text_to_copy = edit_text.get("1.0", "end-1c") if edit_text else _last_output
        pyperclip.copy(text_to_copy)

        messagebox.showinfo("복사 완료", "생성된 문구가 클립보드에 복사되었습니다.")
    except Exception as e:
        messagebox.showerror("복사 실패", str(e))

button_2박3일 = tk.Button(input_frame, text="2박3일 예약 전환", command=모드전환)
button_2박3일.grid(row=len(label_texts)+1, column=0, columnspan=2, pady=5)

button_출력 = tk.Button(input_frame, text="📋 예약 출력", command=예약확인)
button_출력.grid(row=len(label_texts)+2, column=0, columnspan=2, pady=2)

button_복사 = tk.Button(input_frame, text="📋 결과 복사", command=결과복사)
button_복사.grid(row=len(label_texts)+3, column=0, columnspan=2, pady=2)

button_저장 = tk.Button(input_frame, text="💾 예약 기록 저장", command=lambda: 저장())
button_저장.grid(row=len(label_texts)+4, column=0, columnspan=2, pady=2)

button_편집 = tk.Button(input_frame, text="✍ 직접 수정", command=_open_editor)
button_편집.grid(row=len(label_texts)+5, column=0, columnspan=2, pady=2)

# [NEW] 언제든 홈으로
button_처음 = tk.Button(input_frame, text="⬅ 처음으로", command=lambda: show_home())
button_처음.grid(row=len(label_texts)+6, column=0, columnspan=2, pady=2)

def show_home():
    """처음 화면으로"""
    try:
        # 패키지 화면 숨기기
        input_frame.grid_remove()
        text_canvas.grid_remove()
        scrollbar.grid_remove()
        ban_frame.grid_remove()
        prep_frame.grid_remove()   # [NEW] 준비중 화면 숨김
    except Exception:
        pass
    # 홈 보이기
    home_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")
def show_pkg():
    """패키지 문자 화면으로"""
    # 홈 숨기기
    home_frame.grid_remove()
    # 패키지 화면 보이기 (원래 배치 그대로)
    input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="n")
    text_canvas.grid(row=0, column=1, rowspan=20, padx=(10,0), pady=10, sticky="nsew")
    scrollbar.grid(row=0, column=2, rowspan=20, sticky="ns", padx=(0,10), pady=10)
    # 씹덕모드일 땐 우측 배경 재크롭
    _update_canvas_bg()
def show_ban():
    """금지목록 화면으로"""
    try:
        input_frame.grid_remove()
        text_canvas.grid_remove()
        scrollbar.grid_remove()
        home_frame.grid_remove()
    except Exception:
        pass
    ban_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")
    ban_input.focus_set()
    _ban_reload_from_disk()  # ← 이 줄 추가: 화면 들어올 때 항상 최신 목록으로
    try:
         ban_result.config(text="가능: 07:30 이후, 12:30 이후 가능", fg="#2e7d32")
    except Exception:
         pass
    # placeholder를 초기화(빈칸이면 "여기에 이름입력" 세팅)
    try:
        _ban_ph_out()
    except Exception:
        pass
# ===== [NEW] 준비중(템플릿 문자) 로직 =====
def _prep_build_list():
    """검색어로 TEMPLATES 필터링하여 리스트 갱신"""
    key = prep_search.get().strip()
    prep_list.delete(0, tk.END)
    items = [name for name in TEMPLATES.keys()
             if not key or (key in name)]
    for name in items:
        prep_list.insert(tk.END, name)
def _prep_clear_form():
    for w in prep_form.winfo_children():
        w.destroy()
    _prep_fields.clear()
def _bind_auto(entry, kind: str | None):
    """date/time/price 자동입력 바인딩"""
    if kind == "date":
        entry.bind("<KeyRelease>", lambda e, 구분="/": 자동입력(e, 구분))
    elif kind == "time":
        entry.bind("<KeyRelease>", lambda e, 구분=":": 자동입력(e, 구분))
    elif kind == "price":
        entry.bind("<KeyRelease>", lambda e, 구분=",": 자동입력(e, 구분))
def _prep_build_form(tpl_name: str):
    """선택된 템플릿의 입력 폼 생성"""
    _prep_clear_form()
    _prep_selected.set(tpl_name)
    spec = TEMPLATES[tpl_name]
    for r, (label_txt, key, *typeopt) in enumerate(spec["fields"], start=0):
        kind = typeopt[0] if typeopt else None
        tk.Label(prep_form, text=label_txt, bg=기본테마["배경"], fg=기본테마["라벨글자"])\
            .grid(row=r, column=0, sticky="w", pady=2, padx=(0,6))
        e = tk.Entry(prep_form, width=22, bg=기본테마["입력창배경"])
        e.grid(row=r, column=1, sticky="w", pady=2)
        _bind_auto(e, kind)
        _prep_fields[key] = e
    # 입력 변경 시마다 바로 렌더링
    for e in _prep_fields.values():
        e.bind("<KeyRelease>", lambda _e: _prep_render(), add="+")
    _prep_render()
class _SafeFormatDict(dict):
    defaults = {
        "name": "미정",
        "날짜": "미정",
        "시간": "미정",
    }
    def __missing__(self, key):
        return ""
def _prep_render():
    """현재 폼 값으로 텍스트 출력"""
    if not _prep_selected.get():
        return
    spec = TEMPLATES[_prep_selected.get()]
    data = {k: _prep_fields[k].get().strip() for k in _prep_fields}
    # ── 파생 날짜 키 자동 생성: {날짜-3}, {날짜+1} 같은 것 지원 ──
    from datetime import timedelta
    for k, v in list(data.items()):
        if _is_valid_mmdd(v):  # 이미 있는 유틸 함수 사용
            base = _mmdd_to_dt(v, datetime.now().year)
            for off in (1, 2, 3, 7):  # 필요하면 숫자 더 추가
                data[f"{k}-{off}"] = (base - timedelta(days=off)).strftime("%m/%d")
                data[f"{k}+{off}"] = (base + timedelta(days=off)).strftime("%m/%d")
    out = spec["format"].format_map(_SafeFormatDict(data))
    # 텍스트 갱신
    prep_text.config(state="normal")
    prep_text.delete("1.0", "end")
    prep_text.insert("1.0", out)
    prep_text.config(state="disabled")
def _prep_copy():
    try:
        pyperclip.copy(prep_text.get("1.0", "end-1c"))
        messagebox.showinfo("복사", "출력 내용을 복사했습니다.")
    except Exception as e:
        messagebox.showerror("복사 실패", str(e))
def _prep_enable_edit():
    """파란칸 직접수정 가능 토글"""
    state = str(prep_text.cget("state"))
    if state == "disabled":
        prep_text.config(state="normal")
    else:
        prep_text.config(state="disabled")
def show_prep():
    """준비중(템플릿) 화면으로"""
    try:
        input_frame.grid_remove()
        text_canvas.grid_remove()
        scrollbar.grid_remove()
        home_frame.grid_remove()
        ban_frame.grid_remove()
    except Exception:
        pass
    prep_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")
    _prep_build_list()
    prep_search.focus_set()

# 이벤트 바인딩(검색/선택)
prep_search.bind("<KeyRelease>", lambda e: _prep_build_list())
prep_list.bind("<<ListboxSelect>>",
               lambda e: (_prep_build_form(prep_list.get(prep_list.curselection()[0]))
                          if prep_list.curselection() else None))
def _ban_check(entry_widget, result_label):
    text = entry_widget.get().strip()
    if not text or text == PLACEHOLDER:                # ← 조건 보강
        result_label.config(text="이름을 입력하세요.", fg="#d32f2f")
        return
    if any(name in text for name in 노캐디금지목록):
        result_label.config(text="노캐디 불가", fg="#d32f2f")
    elif any(name in text for name in 오인플금지목록):
        result_label.config(text="5인플 불가", fg="#d32f2f")
    else:
        result_label.config(text="가능: 07:30 이후, 12:30 이후 가능", fg="#2e7d32")
def _ban_copy(result_label):
    try:
        pyperclip.copy(result_label.cget("text"))
        messagebox.showinfo("복사", "결과를 클립보드로 복사했습니다.")
    except Exception as e:
        messagebox.showerror("복사 실패", str(e))
def 저장():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    month_folder = datetime.now().strftime("%Y%m")
    save_dir = os.path.join(desktop, "패키지예약", month_folder)
    os.makedirs(save_dir, exist_ok=True)

    filename = os.path.join(save_dir, "예약기록.txt")
    with open(filename, "a", encoding="utf-8") as f:
        예약당일 = datetime.now().strftime("%Y-%m-%d")
        예약일 = W["day1.date"].get()
        예약자명 = W["name"].get()
        f.write(f"{예약당일} - {예약일} - {예약자명}\n")
# 좌하단에 배치하지만 배경색과 동일하게 해서 숨긴 것처럼 보이게
def 토글테마():
    """
    테마 전환 + 배경/오버레이 + 숨김버튼(좌하단) 고정/최상단 유지.
    - 숨김버튼은 창 크기 변경에도 항상 좌하단(sw) 모서리에 붙도록 place(relx/rely) 사용
    - 클릭 안 되던 이슈 방지: 전환 직후와 매 Configure 이벤트마다 재배치 + lift()
    - 입력 패널(왼쪽 Frame) 위에만 반투명 오버레이를 얹고, 그 위젯들은 항상 최상단으로 유지
    """
    global img_label, overlay_labels, hidden_button
    # --- 숨김버튼을 좌하단에 고정하는 헬퍼 ---
    def _place_hidden_button():
        try:
            root.update_idletasks()
            bg = root.cget("bg")
            hidden_button.configure(
                text=" ", width=3, height=1,  # 클릭영역 넉넉히
                bg=bg, fg=bg,
                activebackground=bg, activeforeground=bg,
                relief="flat", bd=0, highlightthickness=0,
                takefocus=0, cursor="arrow",
            )
            # 창 좌하단 고정 (모서리 기준 sw)
            hidden_button.place(in_=root, relx=0, rely=1, x=8, y=-8, anchor="sw")
            hidden_button.lift()  # 항상 최상단
        except Exception:
            pass
    # 창 리사이즈 때도 항상 제자리에
    if not getattr(root, "_hb_place_bound", False):
        root.bind("<Configure>", lambda e: _place_hidden_button())
        setattr(root, "_hb_place_bound", True)
    현재배경 = root.cget("bg")
    if 현재배경 == 기본테마["배경"]:
        # ===== 씹덕테마 적용 =====
        root.configure(bg=씹덕테마["배경"])
        input_frame.configure(bg=씹덕테마["배경"])
        text_canvas.configure(bg=씹덕테마["출력창배경"])
        for lbl in labels_위젯들:
            lbl.configure(bg=씹덕테마["배경"], fg=씹덕테마["라벨글자"])
        for entry in entry_widgets:
            entry.configure(bg=씹덕테마["입력창배경"])
        # 위젯 실제 좌표/크기 먼저 계산되도록
        root.update_idletasks()
        try:
            # 1) 전체 배경
            base_img = Image.open(os.path.join(BASE_DIR, "hum.jpg")).convert("RGBA")
            base_img = base_img.resize((root.winfo_width(), root.winfo_height()))
            root._bg_base = base_img   # 창 크기에 맞춰 리사이즈된 원본을 전역에 보관
            bg_img = base_img.copy(); bg_img.putalpha(150)  # 창 전체 뒷배경 투명도
            bg_tk = ImageTk.PhotoImage(bg_img)

            # root 최하단에 전체 배경 이미지
            global img_label
            img_label = tk.Label(root, image=bg_tk, bg=씹덕테마["배경"], bd=0)
            img_label.image = bg_tk
            img_label.place(x=0, y=0, relwidth=1, relheight=1)
            img_label.lower()  # 최하단

            # 2) 왼쪽 입력 패널에만 반투명 오버레이 (부모 = input_frame)
            fw, fh = input_frame.winfo_width(), input_frame.winfo_height()
            abs_x = input_frame.winfo_rootx() - root.winfo_rootx()
            abs_y = input_frame.winfo_rooty() - root.winfo_rooty()

            cropped = base_img.crop((abs_x, abs_y, abs_x + fw, abs_y + fh))
            cropped.putalpha(120)  # 패널 투명도
            cropped_tk = ImageTk.PhotoImage(cropped)

            panel_bg = tk.Label(input_frame, image=cropped_tk, bd=0, highlightthickness=0)
            panel_bg.image = cropped_tk
            panel_bg.place(x=0, y=0, width=fw, height=fh)

            # 오버레이/배경 Z-순서 정리
            panel_bg.lower()                # frame의 바닥
            for child in input_frame.winfo_children():
                if child is not panel_bg:
                    child.lift()           # 입력창/버튼 등은 항상 오버레이 위로

            global overlay_labels
            overlay_labels = [panel_bg]
            # [NEW] 텍스트영역 워터마크 적용 + 리사이즈에도 갱신
            _update_canvas_bg()
            if not getattr(text_canvas, "_bg_bind", False):
                text_canvas.bind("<Configure>", lambda e: _update_canvas_bg(), add="+")
                root.bind("<Configure>",       lambda e: _update_canvas_bg(), add="+")
                text_canvas._bg_bind = True
        except Exception as e:
            print("이미지 처리 실패:", e)    
        # 숨김버튼은 항상 최상단/좌하단 고정
        _place_hidden_button()
    else:
        # ===== 기본테마 복구 =====
        root.configure(bg=기본테마["배경"])
        input_frame.configure(bg=기본테마["배경"])
        text_canvas.configure(bg=기본테마["출력창배경"])
        for lbl in labels_위젯들:
            lbl.configure(bg=기본테마["배경"], fg=기본테마["라벨글자"])
        for entry in entry_widgets:
            entry.configure(bg=기본테마["입력창배경"])
        # 만들어둔 라벨 정리
        try:
            if img_label.winfo_exists():
                img_label.destroy()
        except Exception:
            pass
        try:
            for lbl in overlay_labels:
                if lbl.winfo_exists():
                    lbl.destroy()
        except Exception:
            pass
        overlay_labels = []
        root._text_bg_label = None
        _update_canvas_bg()  # 전환 직후 폭/배경 즉시 재계산 (일반모드)
        # 복귀 후에도 숨김 버튼은 항상 위/좌하단 고정
        _place_hidden_button()
# --- 숨김(토글) 버튼을 생성/배치: 프로그램 초기화가 끝난 뒤 한 번 호출하세요 ---
# 예) 모든 위젯 배치가 끝난 뒤: init_hidden_toggle_button(root)
def init_hidden_toggle_button(root):
    global hidden_button
    try:
        hidden_button.destroy()
    except Exception:
        pass
    hidden_button = tk.Button(
        root,
        command=토글테마,
        text=" ",  # 내용은 숨김
        relief="flat", bd=0, highlightthickness=0,
        takefocus=0, cursor="arrow",
    )
    def _place(_=None):
        bg = root.cget("bg")
        hidden_button.configure(bg=bg, activebackground=bg, fg=bg, activeforeground=bg, width=3, height=1)
        hidden_button.place(in_=root, relx=0, rely=1, x=8, y=-8, anchor="sw")
        hidden_button.lift()
    # 처음에도, 리사이즈 때도 항상 좌하단/최상단 유지
    root.bind("<Configure>", _place, add="+")
    root.after(0, _place)
    # 키보드 단축키도 함께: Ctrl+Shift+T
    root.bind("<Control-Shift-t>", lambda e: 토글테마(), add="+")
# … 위젯들(grid/place) 다 끝난 다음
root.update_idletasks()             # 크기/좌표 계산
init_hidden_toggle_button(root)     # ⬅️ 이 줄 추가 (숨김 버튼 + 단축키 등록)
# [NEW] 앱 시작하면 처음 화면부터
show_home()

root.bind("<Control-e>", lambda e: (_open_editor(), "break"), add="+")

root.mainloop()
