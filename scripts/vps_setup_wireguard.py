#!/usr/bin/env python3
"""SSH into VPS and set up WireGuard server"""
import paramiko
import sys
import time

VPS_IP = "185.113.249.211"
VPS_USER = "root"
VPS_PASS = "pUZ9z0m5mFK@"

# Windows client public key (generated on this machine)
CLIENT_PUBKEY = "Uy0B6B6HSzD+31a5QLnPpzSjNbjt0hyTE/duCBcJ1xE="

def run_cmd(ssh, cmd, timeout=60):
    """Run a command and return output"""
    print(f"  > {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        print(f"    {out[:500]}")
    if err and 'WARNING' not in err.upper():
        print(f"    [stderr] {err[:300]}")
    return out, err

def main():
    print(f"Connecting to {VPS_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=15)
        print("Connected!\n")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    # Step 1: Check OS and install WireGuard
    print("=== Step 1: Install WireGuard ===")
    run_cmd(ssh, "cat /etc/os-release | head -3")
    run_cmd(ssh, "apt-get update -qq && apt-get install -y wireguard wireguard-tools", timeout=120)

    # Step 2: Enable IP forwarding
    print("\n=== Step 2: Enable IP forwarding ===")
    run_cmd(ssh, "echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf && sysctl -p")

    # Step 3: Generate server keys
    print("\n=== Step 3: Generate WireGuard server keys ===")
    run_cmd(ssh, "mkdir -p /etc/wireguard")
    run_cmd(ssh, "wg genkey | tee /etc/wireguard/server_private.key | wg pubkey > /etc/wireguard/server_public.key")
    run_cmd(ssh, "chmod 600 /etc/wireguard/server_private.key")

    server_privkey, _ = run_cmd(ssh, "cat /etc/wireguard/server_private.key")
    server_pubkey, _ = run_cmd(ssh, "cat /etc/wireguard/server_public.key")

    print(f"\n  Server Private Key: {server_privkey}")
    print(f"  Server Public Key:  {server_pubkey}")

    # Step 4: Find the main network interface
    print("\n=== Step 4: Detect network interface ===")
    iface, _ = run_cmd(ssh, "ip route | grep default | awk '{print $5}' | head -1")
    print(f"  Main interface: {iface}")

    # Step 5: Create WireGuard server config
    print("\n=== Step 5: Create WireGuard server config ===")
    wg_config = f"""[Interface]
PrivateKey = {server_privkey}
Address = 10.66.66.1/24
ListenPort = 51820
PostUp = iptables -t nat -A POSTROUTING -o {iface} -j MASQUERADE; iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -o {iface} -j MASQUERADE; iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT

[Peer]
# Windows EC2 Client
PublicKey = {CLIENT_PUBKEY}
AllowedIPs = 10.66.66.2/32
"""

    # Write config via heredoc
    run_cmd(ssh, f"cat > /etc/wireguard/wg0.conf << 'WGEOF'\n{wg_config}\nWGEOF")
    run_cmd(ssh, "chmod 600 /etc/wireguard/wg0.conf")

    # Step 6: Open firewall port
    print("\n=== Step 6: Open firewall port 51820 ===")
    run_cmd(ssh, "ufw allow 51820/udp 2>/dev/null; iptables -A INPUT -p udp --dport 51820 -j ACCEPT")

    # Step 7: Start WireGuard
    print("\n=== Step 7: Start WireGuard ===")
    run_cmd(ssh, "systemctl enable wg-quick@wg0")
    run_cmd(ssh, "systemctl restart wg-quick@wg0")

    # Step 8: Verify
    print("\n=== Step 8: Verify WireGuard is running ===")
    run_cmd(ssh, "wg show")

    # Step 9: Also push our SSH key while we're at it
    print("\n=== Step 9: Push SSH key ===")
    with open("C:\\Users\\Administrator\\.ssh\\id_ed25519.pub", "r") as f:
        pubkey = f.read().strip()
    run_cmd(ssh, f"mkdir -p ~/.ssh && echo '{pubkey}' >> ~/.ssh/authorized_keys && sort -u -o ~/.ssh/authorized_keys ~/.ssh/authorized_keys")

    ssh.close()

    # Output the client config
    print("\n" + "="*60)
    print("  WIREGUARD SETUP COMPLETE!")
    print("="*60)
    print(f"\nServer Public Key: {server_pubkey}")
    print(f"Server Endpoint:   {VPS_IP}:51820")
    print(f"Client IP:         10.66.66.2/32")
    print(f"\nWindows client config to write to wg0.conf:")
    print("-"*60)

    client_config = f"""[Interface]
PrivateKey = IOKc1RK03zqC2WJPWL+UiZKNkbONqefu1sODQ1z8014=
Address = 10.66.66.2/24
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = {server_pubkey}
Endpoint = {VPS_IP}:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
    print(client_config)
    print("-"*60)

    # Save client config
    config_path = "C:\\Users\\Administrator\\wg_client.conf"
    with open(config_path, "w") as f:
        f.write(client_config)
    print(f"\nClient config saved to: {config_path}")


if __name__ == "__main__":
    main()
