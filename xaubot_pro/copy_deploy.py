import shutil, os, sys
sys.stdout.reconfigure(encoding='utf-8')

src = r"c:\Users\User\OneDrive\Desktop\viral_tiktok_bot\_old_files"
dst = os.path.join(src, "deploy_package")
os.makedirs(dst, exist_ok=True)

files = [
    "app.py", "live_bot.py", "trade.py", "config.json", "requirements.txt",
]
for f in files:
    s = os.path.join(src, f)
    d = os.path.join(dst, f)
    if os.path.exists(s):
        shutil.copy2(s, d)
        print(f"  Copied {f} ({os.path.getsize(d)} bytes)")
    else:
        print(f"  MISSING {f}")

# Streamlit config
s = os.path.join(src, ".streamlit", "config.toml")
d = os.path.join(dst, "config.toml")
if os.path.exists(s):
    shutil.copy2(s, d)
    print(f"  Copied config.toml")

# Landing page
s = os.path.join(src, "landing", "index.html")
d = os.path.join(dst, "index.html")
if os.path.exists(s):
    shutil.copy2(s, d)
    print(f"  Copied index.html")

s = os.path.join(src, "landing", "server.py")
d = os.path.join(dst, "server.py")
if os.path.exists(s):
    shutil.copy2(s, d)
    print(f"  Copied server.py")

print("\nDeploy package ready!")
print(f"Contents of {dst}:")
for f in os.listdir(dst):
    print(f"  {f} ({os.path.getsize(os.path.join(dst, f))} bytes)")
