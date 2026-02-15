import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
import paramiko
print("paramiko OK", paramiko.__version__)
