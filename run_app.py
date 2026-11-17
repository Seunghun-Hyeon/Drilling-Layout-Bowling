import os
import sys
import socket
import threading
import time
import webbrowser
import streamlit.web.cli as stcli

def get_resource_path(relative_path):
    """PyInstaller로 패키징된 내부 리소스 경로 반환"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def get_free_port():
    """사용 가능한 빈 로컬 포트 찾기"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def open_browser(port):
    """서버 준비 후 기본 브라우저 자동 오픈"""
    time.sleep(2.5)
    webbrowser.open(f"http://localhost:{port}")

if __name__ == "__main__":
    # .exe 파일이 위치한 실제 디렉토리로 작업 경로 고정 (presets.json 영구 저장용)
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        os.chdir(exe_dir)

    app_path = get_resource_path("bowling_sim_app.py")
    port = get_free_port()

    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        f"--server.port={port}",
        "--server.address=localhost",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]
    sys.exit(stcli.main())