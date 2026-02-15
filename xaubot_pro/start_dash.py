import subprocess
PYTHON = r'C:\Users\User\OneDrive\Desktop\viral_tiktok_bot\.venv\Scripts\python.exe'
p = subprocess.Popen(
    [PYTHON, '-m', 'streamlit', 'run', 'app.py', '--server.port', '8501', '--server.headless', 'true'],
    cwd=r'c:\Users\User\OneDrive\Desktop\viral_tiktok_bot\_old_files',
    creationflags=0x00000008
)
print(f'Dashboard started PID {p.pid}')
print('Open http://localhost:8501')
