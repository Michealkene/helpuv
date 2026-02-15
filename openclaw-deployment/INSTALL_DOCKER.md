# Installing Docker Desktop for Windows

## Quick Install

### Option 1: Direct Download (Recommended)

1. **Download Docker Desktop:**
   - Go to: https://www.docker.com/products/docker-desktop/
   - Click "Download for Windows"
   - Or direct link: https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe

2. **Run the installer:**
   - Double-click `Docker Desktop Installer.exe`
   - Follow the installation wizard
   - **Important:** Enable WSL 2 when prompted (recommended)

3. **Restart your computer** after installation

4. **Start Docker Desktop:**
   - Find "Docker Desktop" in your Start menu
   - Launch it
   - Wait for it to start (you'll see a Docker icon in your system tray)

5. **Verify installation:**
   ```powershell
   docker --version
   docker-compose --version
   ```

### Option 2: Using Winget (if available)

```powershell
winget install Docker.DockerDesktop
```

## Post-Installation

Once Docker is installed and running:

```powershell
# Verify Docker is running
docker ps

# If you see this, Docker is ready:
# CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

## Next Steps

After Docker is installed, return to the deployment directory and run:

```powershell
cd C:\Users\Administrator\openclaw-deployment\shared-scripts
.\manage-all.ps1 setup
```

## Troubleshooting

### "Docker daemon not running"

- Make sure Docker Desktop is running (check system tray)
- Restart Docker Desktop
- Restart your computer

### WSL 2 Installation Issues

If WSL 2 installation fails:
```powershell
# Run as Administrator
wsl --install
wsl --set-default-version 2
```

### Permission Issues

Run PowerShell as Administrator for Docker commands.
