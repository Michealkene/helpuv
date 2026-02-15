# Cherry Studio Database Connection Info

## ✅ Installation Complete
- **Cherry Studio Version:** 1.7.17
- **Installed Location:** `C:\Users\Administrator\AppData\Local\Programs\Cherry Studio\`
- **Executable:** `C:\Users\Administrator\AppData\Local\Programs\Cherry Studio\Cherry Studio.exe`

## 📁 Database Location
**Main Database:** `C:\Users\Administrator\AppData\Roaming\CherryStudio\agents.db`

**Type:** SQLite 3  
**Size:** Created on first run

## 🔌 How to Connect

### Option 1: SQLite Browser (GUI - Recommended)
1. Download from: https://sqlitebrowser.org/dl/
2. Install and open "DB Browser for SQLite"
3. Click "Open Database"
4. Navigate to: `C:\Users\Administrator\AppData\Roaming\CherryStudio\agents.db`

### Option 2: Command Line (sqlite3)
```bash
# Download SQLite CLI from: https://www.sqlite.org/download.html
sqlite3 "C:\Users\Administrator\AppData\Roaming\CherryStudio\agents.db"

# Once inside:
.tables              # List all tables
.schema agents       # Show table structure
SELECT * FROM agents LIMIT 10;
```

### Option 3: Python
```python
import sqlite3

conn = sqlite3.connect(r'C:\Users\Administrator\AppData\Roaming\CherryStudio\agents.db')
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cursor.fetchall())

conn.close()
```

### Option 4: Node.js
```javascript
const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('C:\\Users\\Administrator\\AppData\\Roaming\\CherryStudio\\agents.db');

db.all("SELECT name FROM sqlite_master WHERE type='table'", [], (err, rows) => {
  console.log(rows);
});
```

### Option 5: Direct Connection String
```
Data Source=C:\Users\Administrator\AppData\Roaming\CherryStudio\agents.db;Version=3;
```

## 📂 Other Important Files
- **Config:** `C:\Users\Administrator\AppData\Roaming\CherryStudio\config.json`
- **Logs:** `C:\Users\Administrator\AppData\Roaming\CherryStudio\logs\`
- **Cache:** `C:\Users\Administrator\AppData\Roaming\CherryStudio\Cache\`

## 🌐 Web Access
Cherry Studio also uses:
- **IndexedDB:** `C:\Users\Administrator\AppData\Roaming\CherryStudio\IndexedDB\`
- **Local Storage:** `C:\Users\Administrator\AppData\Roaming\CherryStudio\Local Storage\`

## 📊 Quick Download Links
- **SQLite Browser:** https://sqlitebrowser.org/dl/
- **SQLite CLI Tools:** https://www.sqlite.org/download.html

---

**Created:** 2026-02-10 18:56 UTC  
**Cherry Studio GitHub:** https://github.com/CherryHQ/cherry-studio
