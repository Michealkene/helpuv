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
    "src/main.tsx",
    "src/index.css",
    "src/pages/Login.tsx",
    "src/pages/Signup.tsx",
    "src/pages/Dashboard.tsx",
    "src/pages/Search.tsx",
    "src/pages/Leads.tsx",
    "src/pages/LeadDetail.tsx",
    "src/pages/Campaigns.tsx",
    "src/pages/CampaignDetail.tsx",
    "src/pages/CampaignCreate.tsx",
    "src/pages/Agents.tsx",
    "src/pages/Analytics.tsx",
    "src/pages/Billing.tsx",
    "src/pages/Settings.tsx",
    "src/pages/VoiceAI.tsx",
    "src/components/Sidebar.tsx",
    "src/components/Layout.tsx",
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
