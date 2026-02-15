import paramiko
import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

host = "185.113.249.211"
user = "root"
password = "pUZ9z0m5mFK@"

cmd = sys.argv[1] if len(sys.argv) > 1 else "echo connected"
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 30

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(host, username=user, password=password, timeout=15)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print(out, end='')
    if err:
        print(err, end='', file=sys.stderr)
    sys.exit(stdout.channel.recv_exit_status())
except Exception as e:
    print(f"SSH Error: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    client.close()
