import paramiko
import os

host = "185.113.249.211"
user = "root"
password = "pUZ9z0m5mFK@"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=10)

sftp = client.open_sftp()

base = "C:/Users/Administrator/Desktop/helpuvio-frontend"
remote_base = "/var/www/helpuvio/frontend"

files = [
    "src/components/Sidebar.tsx",
    "src/pages/Dashboard.tsx",
]

for f in files:
    local = os.path.join(base, f).replace(os.sep, "/")
    remote = remote_base + "/" + f
    print(f"Uploading {f}...", end=" ")
    sftp.put(local, remote)
    print("done")

sftp.close()
client.close()
print("All files uploaded!")
