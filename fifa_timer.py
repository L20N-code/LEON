import tkinter as tk
from tkinter import messagebox
import time
import threading
import os
import sys
import urllib.request
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone

# 한국 표준시(KST) 설정 및 전역 변수
KST = timezone(timedelta(hours=9))
time_offset = timedelta(0) 
is_running = False
target_hour = 0
target_minute = 0

def resource_path(relative_path):
    """ PyInstaller 내부 임시 폴더에서 리소스 파일의 절대 경로를 가져옵니다. """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def sync_server_time():
    """피파 공식 홈페이지의 서버 시간을 가져와 내 PC와의 오차를 계산합니다."""
    global time_offset
    try:
        lbl_current.config(text="서버 시간 동기화 중...")
        req = urllib.request.Request("https://fconline.nexon.com", method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)') 
        
        with urllib.request.urlopen(req, timeout=5) as response:
            date_str = response.headers['Date']
            server_time_utc = parsedate_to_datetime(date_str)
            server_time_kst = server_time_utc.astimezone(KST)
            
            local_time = datetime.now(KST)
            time_offset = server_time_kst - local_time
            return True
    except Exception as e:
        messagebox.showwarning("동기화 실패", "서버 시간을 가져오지 못해 PC 시간을 기준으로 작동합니다.")
        time_offset = timedelta(0)
        return False

def check_time():
    """백그라운드에서 오차를 반영한 서버 시간을 확인하고 동작을 수행하는 함수"""
    while is_running:
        now_server_time = datetime.now(KST) + time_offset
        current_time_str = now_server_time.strftime("%H:%M:%S")
        lbl_current.config(text=f"피파 서버 시간: {current_time_str}")
        
        if now_server_time.hour == target_hour and now_server_time.minute == target_minute and now_server_time.second == 0:
            action = action_var.get()
            if action == "shutdown":
                os.system("shutdown /s /f /t 0")
            elif action == "restart":
                os.system("shutdown /r /f /t 0")
            break
        time.sleep(1)

def start_timer():
    """타이머 시작"""
    global is_running, target_hour, target_minute
    try:
        target_hour = int(entry_hour.get())
        target_minute = int(entry_min.get())
        
        if not (0 <= target_hour <= 23 and 0 <= target_minute <= 59):
            raise ValueError
        
        sync_server_time()
        
        is_running = True
        btn_start.config(state=tk.DISABLED)
        btn_stop.config(state=tk.NORMAL)
        
        action_text = "종료" if action_var.get() == "shutdown" else "다시 시작"
        messagebox.showinfo("예약 완료", f"피파 서버 시간 기준\n{target_hour}시 {target_minute}분에 PC가 {action_text}됩니다.")
        
        threading.Thread(target=check_time, daemon=True).start()
    except ValueError:
        messagebox.showerror("입력 오류", "0~23시, 0~59분 사이의 숫자를 정확히 입력해주세요.")

def stop_timer():
    """타이머 취소"""
    global is_running
    is_running = False
    btn_start.config(state=tk.NORMAL)
    btn_stop.config(state=tk.DISABLED)
    lbl_current.config(text="현재 시간: -")

# 1. 메인 윈도우 설정
root = tk.Tk()
root.title("피파 점검 대비 PC 종료 및 다시 시작 관리기")
root.geometry("450x250")

# 윈도우 작업 표시줄에 고유 ID를 부여하여 파이썬 기본 아이콘 분리 (작업표시줄 깃털 방지)
import ctypes
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("mycompany.pchandler.autosutdown.1")
except Exception:
    pass

# 내부 압축 해제된 경로에서 아이콘 로드
try:
    root.iconbitmap(resource_path('soccer.ico'))
except Exception:
    pass 

# 2. 동작 선택 라디오 버튼
action_var = tk.StringVar(value="shutdown")

frame_action = tk.Frame(root)
frame_action.pack(pady=(15, 5))

tk.Radiobutton(frame_action, text="시스템 종료", variable=action_var, value="shutdown").pack(side=tk.LEFT, padx=10)
tk.Radiobutton(frame_action, text="다시 시작", variable=action_var, value="restart").pack(side=tk.LEFT, padx=10)

# 3. 시간 입력부
tk.Label(root, text="시간을 입력하세요 (24시간제)", font=("", 10, "bold")).pack(pady=10)

frame_time = tk.Frame(root)
frame_time.pack()

entry_hour = tk.Entry(frame_time, width=5, justify='center')
entry_hour.pack(side=tk.LEFT)
tk.Label(frame_time, text="시 ").pack(side=tk.LEFT)

entry_min = tk.Entry(frame_time, width=5, justify='center')
entry_min.pack(side=tk.LEFT)
tk.Label(frame_time, text="분").pack(side=tk.LEFT)

# 4. 시간 출력부
lbl_current = tk.Label(root, text="현재 시간: -", fg="blue")
lbl_current.pack(pady=15)

# 5. 제어 버튼
frame_btn = tk.Frame(root)
frame_btn.pack()

btn_start = tk.Button(frame_btn, text="예약 시작", command=start_timer, width=10)
btn_start.pack(side=tk.LEFT, padx=5)

btn_stop = tk.Button(frame_btn, text="예약 취소", command=stop_timer, state=tk.DISABLED, width=10)
btn_stop.pack(side=tk.LEFT, padx=5)

root.mainloop()
