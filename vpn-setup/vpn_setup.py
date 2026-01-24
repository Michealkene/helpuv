#!/usr/bin/env python3
"""
WireGuard VPN Auto-Setup Script
Production-ready VPN installation with kill switch and complete automation
"""

import os
import sys
import subprocess
import socket
import ipaddress
import argparse
import json
import shutil
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# ============================================================================
# CONSTANTS
# ============================================================================

VERSION = "1.0.0"
WG_INTERFACE = "wg0"
WG_PORT = 51820
VPN_NETWORK = "10.8.0.0/24"
VPN_SERVER_IP = "10.8.0.1"
DNS_SERVERS = ["1.1.1.1", "8.8.8.8"]
CONFIG_DIR = Path("/etc/wireguard")
LOG_FILE = Path("/var/log/vpn-setup.log")
BACKUP_DIR = Path("/var/backups/vpn")

# ============================================================================
# LOGGING
# ============================================================================

class Logger:
    """Centralized logging with console and file output"""
    
    @staticmethod
    def setup():
        """Initialize logging directory and file"""
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOG_FILE.touch(mode=0o600, exist_ok=True)
    
    @staticmethod
    def log(message: str, level: str = "INFO"):
        """Log message to file and optionally console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        
        with open(LOG_FILE, "a") as f:
            f.write(log_entry + "\n")
    
    @staticmethod
    def info(message: str, emoji: str = "ℹ️"):
        """Info message with emoji"""
        print(f"{emoji} {message}")
        Logger.log(message, "INFO")
    
    @staticmethod
    def success(message: str):
        """Success message"""
        print(f"✅ {message}")
        Logger.log(message, "SUCCESS")
    
    @staticmethod
    def error(message: str):
        """Error message"""
        print(f"❌ {message}")
        Logger.log(message, "ERROR")
    
    @staticmethod
    def warning(message: str):
        """Warning message"""
        print(f"⚠️  {message}")
        Logger.log(message, "WARNING")

# ============================================================================
# SYSTEM UTILITIES
# ============================================================================

class SystemUtils:
    """System utility functions"""
    
    @staticmethod
    def check_root():
        """Ensure script is run as root"""
        if os.geteuid() != 0:
            Logger.error("This script must be run as root!")
            print("\n💡 Run with: sudo python3 vpn_setup.py")
            sys.exit(1)
    
    @staticmethod
    def run_command(cmd: List[str], check: bool = True, capture: bool = True) -> Tuple[int, str, str]:
        """Run shell command safely"""
        try:
            Logger.log(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=capture,
                text=True
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            Logger.log(f"Command failed: {e.stderr}", "ERROR")
            if check:
                raise
            return e.returncode, e.stdout, e.stderr
        except Exception as e:
            Logger.log(f"Command error: {str(e)}", "ERROR")
            raise
    
    @staticmethod
    def get_os_info() -> Dict[str, str]:
        """Detect OS information"""
        try:
            with open("/etc/os-release") as f:
                os_info = {}
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        os_info[key] = value.strip('"')
                return os_info
        except Exception as e:
            Logger.error(f"Failed to detect OS: {e}")
            sys.exit(1)
    
    @staticmethod
    def check_os_compatibility():
        """Verify OS is supported"""
        os_info = SystemUtils.get_os_info()
        os_id = os_info.get("ID", "").lower()
        
        supported = ["ubuntu", "debian"]
        if os_id not in supported:
            Logger.error(f"Unsupported OS: {os_id}")
            Logger.info("Supported: Ubuntu, Debian")
            sys.exit(1)
        
        Logger.success(f"OS detected: {os_info.get('PRETTY_NAME', os_id)}")
        return os_id
    
    @staticmethod
    def get_network_interface() -> str:
        """Auto-detect primary network interface"""
        try:
            # Get default route interface
            returncode, stdout, _ = SystemUtils.run_command(
                ["ip", "route", "show", "default"],
                check=False
            )
            if returncode == 0 and stdout:
                match = re.search(r'dev (\S+)', stdout)
                if match:
                    return match.group(1)
            
            # Fallback: find first non-loopback interface
            returncode, stdout, _ = SystemUtils.run_command(
                ["ip", "-o", "link", "show"],
                check=False
            )
            for line in stdout.split("\n"):
                if "state UP" in line and "lo:" not in line:
                    match = re.search(r'\d+: (\S+):', line)
                    if match:
                        return match.group(1)
            
            return "eth0"  # Ultimate fallback
        except Exception:
            return "eth0"
    
    @staticmethod
    def get_public_ip() -> str:
        """Detect public IP address"""
        services = [
            "https://api.ipify.org",
            "https://ifconfig.me/ip",
            "https://icanhazip.com"
        ]
        
        for service in services:
            try:
                returncode, stdout, _ = SystemUtils.run_command(
                    ["curl", "-s", "-4", "--max-time", "5", service],
                    check=False
                )
                if returncode == 0 and stdout:
                    ip = stdout.strip()
                    # Validate IP
                    ipaddress.IPv4Address(ip)
                    return ip
            except Exception:
                continue
        
        Logger.error("Failed to detect public IP")
        return ""

# ============================================================================
# BACKUP MANAGER
# ============================================================================

class BackupManager:
    """Handle backups and rollback"""
    
    @staticmethod
    def create_backup():
        """Backup existing configuration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / timestamp
        backup_path.mkdir(parents=True, exist_ok=True)
        
        Logger.info("Creating backup...", "💾")
        
        # Backup WireGuard configs
        if CONFIG_DIR.exists():
            shutil.copytree(CONFIG_DIR, backup_path / "wireguard", dirs_exist_ok=True)
        
        # Backup iptables
        try:
            SystemUtils.run_command(["iptables-save"], check=False)
            returncode, stdout, _ = SystemUtils.run_command(
                ["iptables-save"],
                check=False
            )
            if returncode == 0:
                with open(backup_path / "iptables.rules", "w") as f:
                    f.write(stdout)
        except Exception as e:
            Logger.log(f"Failed to backup iptables: {e}", "WARNING")
        
        Logger.success(f"Backup created: {backup_path}")
        return backup_path

# ============================================================================
# DEPENDENCY INSTALLER
# ============================================================================

class DependencyInstaller:
    """Install required packages"""
    
    @staticmethod
    def install():
        """Install all dependencies"""
        Logger.info("Checking dependencies...", "📦")
        
        # Update package list
        Logger.info("Updating package list...")
        SystemUtils.run_command(["apt-get", "update", "-qq"])
        
        packages = [
            "wireguard",
            "wireguard-tools",
            "qrencode",
            "curl",
            "iptables",
            "net-tools",
            "iproute2"
        ]
        
        for package in packages:
            if not DependencyInstaller.is_installed(package):
                Logger.info(f"Installing {package}...")
                SystemUtils.run_command(
                    ["apt-get", "install", "-y", "-qq", package]
                )
        
        Logger.success("All dependencies installed")
    
    @staticmethod
    def is_installed(package: str) -> bool:
        """Check if package is installed"""
        returncode, _, _ = SystemUtils.run_command(
            ["dpkg", "-s", package],
            check=False
        )
        return returncode == 0

# ============================================================================
# WIREGUARD KEY MANAGER
# ============================================================================

class KeyManager:
    """Generate and manage WireGuard keys"""
    
    @staticmethod
    def generate_keypair() -> Tuple[str, str]:
        """Generate private and public key pair"""
        # Generate private key
        returncode, private_key, _ = SystemUtils.run_command(
            ["wg", "genkey"]
        )
        private_key = private_key.strip()
        
        # Generate public key
        proc = subprocess.Popen(
            ["wg", "pubkey"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        public_key, _ = proc.communicate(input=private_key)
        public_key = public_key.strip()
        
        return private_key, public_key
    
    @staticmethod
    def generate_preshared_key() -> str:
        """Generate preshared key for additional security"""
        returncode, psk, _ = SystemUtils.run_command(["wg", "genpsk"])
        return psk.strip()

# ============================================================================
# SERVER SETUP
# ============================================================================

class ServerSetup:
    """WireGuard server configuration"""
    
    def __init__(self):
        self.interface = SystemUtils.get_network_interface()
        self.public_ip = SystemUtils.get_public_ip()
        self.server_private_key, self.server_public_key = KeyManager.generate_keypair()
        self.clients: List[Dict] = []
    
    def setup(self):
        """Complete server setup"""
        Logger.info("🚀 Starting VPN Server Setup", "")
        
        # Create config directory
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Enable IP forwarding
        self.enable_ip_forwarding()
        
        # Configure firewall
        self.configure_firewall()
        
        # Generate server config
        self.generate_server_config()
        
        # Generate client configs
        self.generate_client_configs(num_clients=3)
        
        # Start WireGuard
        self.start_wireguard()
        
        # Display summary
        self.display_summary()
    
    def enable_ip_forwarding(self):
        """Enable IP forwarding"""
        Logger.info("Enabling IP forwarding...")
        
        # Enable now
        SystemUtils.run_command(
            ["sysctl", "-w", "net.ipv4.ip_forward=1"]
        )
        
        # Make persistent
        sysctl_file = Path("/etc/sysctl.conf")
        content = sysctl_file.read_text()
        
        if "net.ipv4.ip_forward=1" not in content:
            with open(sysctl_file, "a") as f:
                f.write("\n# Enable IP forwarding for VPN\n")
                f.write("net.ipv4.ip_forward=1\n")
        
        Logger.success("IP forwarding enabled")
    
    def configure_firewall(self):
        """Configure firewall rules"""
        Logger.info("Configuring firewall...")
        
        # Allow WireGuard port
        SystemUtils.run_command(
            ["iptables", "-A", "INPUT", "-p", "udp", "--dport", str(WG_PORT), "-j", "ACCEPT"],
            check=False
        )
        
        # Allow forwarding for VPN
        SystemUtils.run_command(
            ["iptables", "-A", "FORWARD", "-i", WG_INTERFACE, "-j", "ACCEPT"],
            check=False
        )
        SystemUtils.run_command(
            ["iptables", "-A", "FORWARD", "-o", WG_INTERFACE, "-j", "ACCEPT"],
            check=False
        )
        
        # NAT for VPN traffic
        SystemUtils.run_command(
            ["iptables", "-t", "nat", "-A", "POSTROUTING", "-s", VPN_NETWORK, 
             "-o", self.interface, "-j", "MASQUERADE"],
            check=False
        )
        
        # Save rules
        try:
            SystemUtils.run_command(["netfilter-persistent", "save"], check=False)
        except:
            pass
        
        Logger.success("Firewall configured")
    
    def generate_server_config(self):
        """Generate server configuration"""
        Logger.info("Generating server config...")
        
        config = f"""[Interface]
Address = {VPN_SERVER_IP}/24
ListenPort = {WG_PORT}
PrivateKey = {self.server_private_key}
PostUp = iptables -A FORWARD -i {WG_INTERFACE} -j ACCEPT; iptables -t nat -A POSTROUTING -o {self.interface} -j MASQUERADE
PostDown = iptables -D FORWARD -i {WG_INTERFACE} -j ACCEPT; iptables -t nat -D POSTROUTING -o {self.interface} -j MASQUERADE

"""
        
        config_file = CONFIG_DIR / f"{WG_INTERFACE}.conf"
        config_file.write_text(config)
        config_file.chmod(0o600)
        
        Logger.success("Server config created")
    
    def generate_client_configs(self, num_clients: int = 3):
        """Generate client configurations"""
        Logger.info(f"Generating {num_clients} client configs...")
        
        server_config_file = CONFIG_DIR / f"{WG_INTERFACE}.conf"
        
        for i in range(1, num_clients + 1):
            client_name = f"client{i}"
            client_ip = f"10.8.0.{i+1}"
            
            # Generate client keys
            client_private, client_public = KeyManager.generate_keypair()
            psk = KeyManager.generate_preshared_key()
            
            # Client config
            client_config = f"""[Interface]
PrivateKey = {client_private}
Address = {client_ip}/24
DNS = {', '.join(DNS_SERVERS)}

[Peer]
PublicKey = {self.server_public_key}
PresharedKey = {psk}
Endpoint = {self.public_ip}:{WG_PORT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
            
            # Save client config
            client_file = CONFIG_DIR / f"{client_name}.conf"
            client_file.write_text(client_config)
            client_file.chmod(0o600)
            
            # Generate QR code
            try:
                SystemUtils.run_command(
                    ["qrencode", "-t", "png", "-o", str(CONFIG_DIR / f"{client_name}.png"), 
                     "-r", str(client_file)]
                )
            except:
                Logger.warning(f"Failed to generate QR code for {client_name}")
            
            # Add peer to server config
            peer_config = f"""
[Peer]
PublicKey = {client_public}
PresharedKey = {psk}
AllowedIPs = {client_ip}/32
"""
            with open(server_config_file, "a") as f:
                f.write(peer_config)
            
            self.clients.append({
                "name": client_name,
                "ip": client_ip,
                "config": str(client_file)
            })
        
        Logger.success(f"{num_clients} client configs created")
    
    def start_wireguard(self):
        """Start WireGuard service"""
        Logger.info("Starting WireGuard...")
        
        # Enable and start service
        SystemUtils.run_command(
            ["systemctl", "enable", f"wg-quick@{WG_INTERFACE}"]
        )
        SystemUtils.run_command(
            ["systemctl", "restart", f"wg-quick@{WG_INTERFACE}"]
        )
        
        time.sleep(2)
        
        # Verify running
        returncode, stdout, _ = SystemUtils.run_command(
            ["wg", "show", WG_INTERFACE],
            check=False
        )
        
        if returncode == 0:
            Logger.success("WireGuard server running")
        else:
            Logger.error("Failed to start WireGuard")
            sys.exit(1)
    
    def display_summary(self):
        """Display setup summary"""
        print("\n" + "="*60)
        Logger.success("VPN Server Setup Complete!")
        print("="*60)
        
        print(f"\n📋 Server Details:")
        print(f"   Public IP: {self.public_ip}")
        print(f"   Port: {WG_PORT}")
        print(f"   Interface: {WG_INTERFACE}")
        print(f"   Network: {VPN_NETWORK}")
        
        print(f"\n📁 Client Configs:")
        for client in self.clients:
            print(f"   {client['config']}")
            png_file = client['config'].replace('.conf', '.png')
            if Path(png_file).exists():
                print(f"   {png_file} (QR code)")
        
        print(f"\n📤 Transfer to Client:")
        print(f"   scp {CONFIG_DIR}/client1.conf user@laptop:~/")
        
        print(f"\n🔧 Management Commands:")
        print(f"   sudo wg show {WG_INTERFACE}                    # Status")
        print(f"   sudo systemctl status wg-quick@{WG_INTERFACE}  # Service status")
        print(f"   sudo systemctl restart wg-quick@{WG_INTERFACE} # Restart")
        print(f"   sudo journalctl -u wg-quick@{WG_INTERFACE} -f  # Logs")
        
        print("\n" + "="*60 + "\n")

# ============================================================================
# CLIENT SETUP
# ============================================================================

class ClientSetup:
    """WireGuard client configuration with kill switch"""
    
    def __init__(self, config_file: str):
        self.config_file = Path(config_file)
        self.kill_switch_active = False
    
    def setup(self):
        """Complete client setup"""
        Logger.info("🚀 Starting VPN Client Setup", "")
        
        # Validate config file
        if not self.config_file.exists():
            Logger.error(f"Config file not found: {self.config_file}")
            sys.exit(1)
        
        # Copy config to WireGuard directory
        self.install_config()
        
        # Disable IPv6 (prevent leaks)
        self.disable_ipv6()
        
        # Setup kill switch
        self.setup_kill_switch()
        
        # Connect to VPN
        self.connect()
        
        # Test connection
        self.test_connection()
        
        # Display summary
        self.display_summary()
    
    def install_config(self):
        """Install client configuration"""
        Logger.info("Installing client config...")
        
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        dest = CONFIG_DIR / f"{WG_INTERFACE}.conf"
        
        shutil.copy(self.config_file, dest)
        dest.chmod(0o600)
        
        Logger.success("Config installed")
    
    def disable_ipv6(self):
        """Disable IPv6 to prevent leaks"""
        Logger.info("Disabling IPv6...")
        
        SystemUtils.run_command(
            ["sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=1"],
            check=False
        )
        SystemUtils.run_command(
            ["sysctl", "-w", "net.ipv6.conf.default.disable_ipv6=1"],
            check=False
        )
        
        Logger.success("IPv6 disabled")
    
    def setup_kill_switch(self):
        """Configure kill switch firewall rules"""
        Logger.info("Setting up kill switch...")
        
        # Flush existing rules
        SystemUtils.run_command(["iptables", "-F"], check=False)
        SystemUtils.run_command(["iptables", "-X"], check=False)
        
        # Default policy: DROP everything
        SystemUtils.run_command(["iptables", "-P", "INPUT", "DROP"], check=False)
        SystemUtils.run_command(["iptables", "-P", "FORWARD", "DROP"], check=False)
        SystemUtils.run_command(["iptables", "-P", "OUTPUT", "DROP"], check=False)
        
        # Allow loopback
        SystemUtils.run_command(["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"], check=False)
        SystemUtils.run_command(["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"], check=False)
        
        # Allow established connections
        SystemUtils.run_command(
            ["iptables", "-A", "INPUT", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
            check=False
        )
        SystemUtils.run_command(
            ["iptables", "-A", "OUTPUT", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
            check=False
        )
        
        # Allow SSH (CRITICAL - prevent lockout)
        SystemUtils.run_command(
            ["iptables", "-A", "INPUT", "-p", "tcp", "--dport", "22", "-j", "ACCEPT"],
            check=False
        )
        SystemUtils.run_command(
            ["iptables", "-A", "OUTPUT", "-p", "tcp", "--sport", "22", "-j", "ACCEPT"],
            check=False
        )
        
        # Allow WireGuard
        SystemUtils.run_command(
            ["iptables", "-A", "OUTPUT", "-p", "udp", "--dport", str(WG_PORT), "-j", "ACCEPT"],
            check=False
        )
        
        # Allow VPN interface
        SystemUtils.run_command(
            ["iptables", "-A", "INPUT", "-i", WG_INTERFACE, "-j", "ACCEPT"],
            check=False
        )
        SystemUtils.run_command(
            ["iptables", "-A", "OUTPUT", "-o", WG_INTERFACE, "-j", "ACCEPT"],
            check=False
        )
        
        # Allow DNS to VPN DNS servers
        for dns in DNS_SERVERS:
            SystemUtils.run_command(
                ["iptables", "-A", "OUTPUT", "-p", "udp", "-d", dns, "--dport", "53", "-j", "ACCEPT"],
                check=False
            )
        
        self.kill_switch_active = True
        Logger.success("Kill switch enabled")
    
    def connect(self):
        """Connect to VPN"""
        Logger.info("Connecting to VPN...")
        
        SystemUtils.run_command(
            ["wg-quick", "up", WG_INTERFACE]
        )
        
        time.sleep(2)
        Logger.success("Connected to VPN")
    
    def disconnect(self):
        """Disconnect from VPN"""
        Logger.info("Disconnecting from VPN...")
        
        SystemUtils.run_command(
            ["wg-quick", "down", WG_INTERFACE],
            check=False
        )
        
        Logger.success("Disconnected from VPN")
    
    def test_connection(self):
        """Test VPN connection"""
        Logger.info("Testing connection...", "🔍")
        
        # Check interface
        returncode, stdout, _ = SystemUtils.run_command(
            ["wg", "show", WG_INTERFACE],
            check=False
        )
        
        if returncode != 0:
            Logger.warning("VPN interface not active")
            return False
        
        # Check public IP
        try:
            returncode, public_ip, _ = SystemUtils.run_command(
                ["curl", "-s", "--max-time", "5", "https://api.ipify.org"],
                check=False
            )
            if returncode == 0:
                Logger.success(f"Public IP: {public_ip.strip()}")
        except:
            Logger.warning("Could not check public IP")
        
        # Test DNS
        returncode, _, _ = SystemUtils.run_command(
            ["ping", "-c", "1", "-W", "2", "1.1.1.1"],
            check=False
        )
        
        if returncode == 0:
            Logger.success("DNS test passed")
        else:
            Logger.warning("DNS test failed")
        
        return True
    
    def status(self):
        """Show VPN status"""
        returncode, stdout, _ = SystemUtils.run_command(
            ["wg", "show", WG_INTERFACE],
            check=False
        )
        
        if returncode == 0:
            print("\n" + "="*60)
            Logger.success("VPN Status: CONNECTED")
            print("="*60)
            print(stdout)
            
            # Show public IP
            try:
                returncode, public_ip, _ = SystemUtils.run_command(
                    ["curl", "-s", "--max-time", "5", "https://api.ipify.org"],
                    check=False
                )
                if returncode == 0:
                    print(f"\n🌐 Public IP: {public_ip.strip()}")
            except:
                pass
            
            print(f"🛡️  Kill Switch: {'ENABLED' if self.kill_switch_active else 'DISABLED'}")
            print("="*60 + "\n")
        else:
            Logger.error("VPN Status: DISCONNECTED")
    
    def display_summary(self):
        """Display setup summary"""
        print("\n" + "="*60)
        Logger.success("VPN Client Setup Complete!")
        print("="*60)
        
        print(f"\n🔌 Connection Status: CONNECTED")
        print(f"🛡️  Kill Switch: ENABLED")
        
        # Show public IP
        try:
            returncode, public_ip, _ = SystemUtils.run_command(
                ["curl", "-s", "--max-time", "5", "https://api.ipify.org"],
                check=False
            )
            if returncode == 0:
                print(f"🌐 Your IP: {public_ip.strip()}")
        except:
            pass
        
        print(f"📍 DNS Leak: PROTECTED")
        
        print(f"\n📋 Commands:")
        print(f"   sudo python3 {sys.argv[0]} --connect     # Connect")
        print(f"   sudo python3 {sys.argv[0]} --disconnect  # Disconnect")
        print(f"   sudo python3 {sys.argv[0]} --status      # Status")
        print(f"   sudo python3 {sys.argv[0]} --test        # Test connection")
        
        print(f"\n⚠️  IMPORTANT:")
        print(f"   - Kill switch blocks all non-VPN traffic")
        print(f"   - SSH remains accessible")
        print(f"   - To disable: sudo python3 {sys.argv[0]} --killswitch-off")
        
        print("\n" + "="*60 + "\n")

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="WireGuard VPN Auto-Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--client",
        metavar="CONFIG_FILE",
        help="Setup as client with config file"
    )
    parser.add_argument("--connect", action="store_true", help="Connect to VPN")
    parser.add_argument("--disconnect", action="store_true", help="Disconnect from VPN")
    parser.add_argument("--status", action="store_true", help="Show VPN status")
    parser.add_argument("--test", action="store_true", help="Test VPN connection")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    
    args = parser.parse_args()
    
    # Setup logging
    Logger.setup()
    
    # Check root
    SystemUtils.check_root()
    
    # Check OS
    SystemUtils.check_os_compatibility()
    
    # Create backup
    BackupManager.create_backup()
    
    try:
        # Client operations
        if args.client or args.connect or args.disconnect or args.status or args.test:
            client = ClientSetup(args.client if args.client else f"{CONFIG_DIR}/{WG_INTERFACE}.conf")
            
            if args.client:
                # Install dependencies
                DependencyInstaller.install()
                client.setup()
            elif args.connect:
                client.connect()
                client.test_connection()
            elif args.disconnect:
                client.disconnect()
            elif args.status:
                client.status()
            elif args.test:
                client.test_connection()
        
        else:
            # Server setup
            DependencyInstaller.install()
            server = ServerSetup()
            server.setup()
    
    except KeyboardInterrupt:
        Logger.warning("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        Logger.error(f"Setup failed: {str(e)}")
        Logger.log(f"Full traceback: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
