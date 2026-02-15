#!/usr/bin/env python3
"""Start a SOCKS5 proxy via SSH tunnel to VPS"""
import paramiko
import threading
import socket
import struct
import select
import sys
import time

VPS_IP = "185.113.249.211"
VPS_USER = "root"
VPS_PASS = "pUZ9z0m5mFK@"
LOCAL_PORT = 1080

class SOCKSProxy:
    def __init__(self, ssh_client, local_port=1080):
        self.ssh = ssh_client
        self.transport = ssh_client.get_transport()
        self.local_port = local_port
        self.server_socket = None
        self.running = False

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('127.0.0.1', self.local_port))
        self.server_socket.listen(50)
        self.server_socket.settimeout(1.0)
        self.running = True
        print(f"SOCKS5 proxy listening on 127.0.0.1:{self.local_port}")
        print(f"Use: --proxy socks5://127.0.0.1:{self.local_port}")

        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                t = threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Accept error: {e}")

    def _handle_client(self, client_sock):
        try:
            # SOCKS5 handshake
            data = client_sock.recv(256)
            if not data or data[0] != 0x05:
                client_sock.close()
                return

            # No auth required
            client_sock.sendall(b'\x05\x00')

            # Get request
            data = client_sock.recv(4)
            if not data or len(data) < 4:
                client_sock.close()
                return

            ver, cmd, _, atyp = data[0], data[1], data[2], data[3]

            if cmd != 0x01:  # Only CONNECT
                client_sock.sendall(b'\x05\x07\x00\x01' + b'\x00'*6)
                client_sock.close()
                return

            # Parse address
            if atyp == 0x01:  # IPv4
                addr_data = client_sock.recv(4)
                dest_addr = socket.inet_ntoa(addr_data)
            elif atyp == 0x03:  # Domain
                addr_len = client_sock.recv(1)[0]
                dest_addr = client_sock.recv(addr_len).decode()
            elif atyp == 0x04:  # IPv6
                addr_data = client_sock.recv(16)
                dest_addr = socket.inet_ntop(socket.AF_INET6, addr_data)
            else:
                client_sock.close()
                return

            port_data = client_sock.recv(2)
            dest_port = struct.unpack('!H', port_data)[0]

            # Open channel through SSH
            try:
                channel = self.transport.open_channel(
                    'direct-tcpip',
                    (dest_addr, dest_port),
                    ('127.0.0.1', 0),
                    timeout=10
                )
            except Exception:
                client_sock.sendall(b'\x05\x05\x00\x01' + b'\x00'*6)
                client_sock.close()
                return

            # Success
            client_sock.sendall(b'\x05\x00\x00\x01' + b'\x00'*4 + b'\x00'*2)

            # Relay data
            self._relay(client_sock, channel)

        except Exception:
            pass
        finally:
            try:
                client_sock.close()
            except:
                pass

    def _relay(self, sock, channel):
        while True:
            r, _, _ = select.select([sock, channel], [], [], 10)
            if not r:
                break

            if sock in r:
                data = sock.recv(32768)
                if not data:
                    break
                channel.sendall(data)

            if channel in r:
                data = channel.recv(32768)
                if not data:
                    break
                sock.sendall(data)

        channel.close()


def main():
    print(f"Connecting to {VPS_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=15)
    print("SSH connected!")

    # Write PID file
    with open("C:\\Users\\Administrator\\socks_proxy.pid", "w") as f:
        import os
        f.write(str(os.getpid()))

    proxy = SOCKSProxy(ssh, LOCAL_PORT)
    try:
        proxy.start()
    except KeyboardInterrupt:
        print("\nStopping proxy...")
        proxy.running = False


if __name__ == "__main__":
    main()
