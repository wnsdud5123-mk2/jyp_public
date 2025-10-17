# launcher.py  (배치 대체용 EXE 런처)
import os, sys, shutil, subprocess, ctypes

SHARE = r"\\10.2.0.113\홍보마케팅\_개인폴더_\이준영\JYP\releases\current"
LOCAL = os.path.join(os.environ.get("LOCALAPPDATA", "."), "JYP", "app")
EXE   = "JYP_예약문자.exe"
VER   = "version.txt"

def msg(text, title="JYP 런처"):
    try:
        ctypes.windll.user32.MessageBoxW(0, str(text), title, 0x40)
    except Exception:
        print(text)

def read_ver(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""

def app_running():
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"IMAGENAME eq {EXE}"],
            text=True, errors="ignore"
        )
        return EXE in out
    except Exception:
        return False

def copy_with_robocopy(src, dst):
    try:
        rc = subprocess.call(
            ["robocopy", src, dst, "/MIR", "/R:1", "/W:1", "/NFL", "/NDL", "/NJH", "/NJS"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return rc < 8  # robocopy 0~7은 성공/경미한 차이
    except Exception:
        return False

def copy_python(src, dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst)

def main():
    os.makedirs(LOCAL, exist_ok=True)

    if app_running():
        msg("앱이 이미 실행 중입니다.")
        return

    remote_ver = read_ver(os.path.join(SHARE, VER))
    local_ver  = read_ver(os.path.join(LOCAL, VER))

    # 업데이트 필요하면 동기화
    if remote_ver and remote_ver != local_ver:
        ok = copy_with_robocopy(SHARE, LOCAL)
        if not ok:
            try:
                copy_python(SHARE, LOCAL)
            except Exception as e:
                msg(f"업데이트 실패:\n{e}")

    exe_local = os.path.join(LOCAL, EXE)
    exe_share = os.path.join(SHARE, EXE)
    target = exe_local if os.path.exists(exe_local) else exe_share

    if not os.path.exists(target):
        msg("실행 파일을 찾을 수 없습니다.\n관리자에게 문의하세요.")
        sys.exit(1)

    DETACHED_PROCESS = 0x00000008
    CREATE_NO_WINDOW = 0x08000000
    subprocess.Popen([target], creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW)

if __name__ == "__main__":
    main()
