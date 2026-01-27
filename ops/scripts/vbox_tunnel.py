import sys
import socket
import select
try:
    import SocketServer as socketserver # Python 2
except ImportError:
    import socketserver # Python 3
import paramiko
import threading
import time

SSH_HOST = '127.0.0.1'
SSH_PORT = 2200
SSH_USER = 'oracle'
SSH_PASS = 'root'

# Forwarding rules based on USER OUTPUT
FORWARDS = [
    # 5000 is bound to 192.168.56.101, NOT localhost.
    # We must bridge to that specific IP from inside the SSH session.
    # LocalPort, RemoteHost(relative to VM), RemotePort
    (5000, '192.168.56.101', 5000), 
    
    # 15789 is bound to localhost (127.0.0.1)
    (15789, '127.0.0.1', 15789),
    
    # Just in case
    (1521, '127.0.0.1', 1521),
    (7803, '127.0.0.1', 7803) 
]

class ForwardServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            chan = self.ssh_transport.open_channel(
                'direct-tcpip',
                (self.chain_host, self.chain_port),
                self.request.getpeername()
            )
        except Exception as e:
            print('Incoming request to %s:%d failed: %s' % (self.chain_host, self.chain_port, repr(e)))
            return

        if chan is None:
            print('Incoming request to %s:%d was rejected by the SSH server.' % (self.chain_host, self.chain_port))
            return

        print('Connected! Tunnel open %r -> %r -> %r' % (self.request.getpeername(),
                                                       chan.getpeername(), (self.chain_host, self.chain_port)))
        while True:
            r, w, x = select.select([self.request, chan], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                self.request.send(data)

        chan.close()
        self.request.close()
        print('Tunnel closed from %r' % (self.request.getpeername(),))

def main():
    print(f"Connecting to {SSH_HOST}:{SSH_PORT} as {SSH_USER}...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(SSH_HOST, SSH_PORT, username=SSH_USER, password=SSH_PASS)
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    print("SSH Connected.")
    transport = client.get_transport()

    for local_port, remote_host, remote_port in FORWARDS:
        class SubHandler(Handler):
            chain_host = remote_host
            chain_port = remote_port
            ssh_transport = transport

        print(f"Forwarding 127.0.0.1:{local_port} -> {remote_host}:{remote_port}")
        try:
            server = ForwardServer(('127.0.0.1', local_port), SubHandler)
            t = threading.Thread(target=server.serve_forever)
            t.setDaemon(True)
            t.start()
        except Exception as e:
            print(f"Could not bind local port {local_port}: {e}")

    print("Tunneling active. Running forever...")
    try:
        while True:
            time.sleep(1)
            if not transport.is_active():
                print("SSH Transport closed.")
                break
    except KeyboardInterrupt:
        print("Stopping...")
        sys.exit(0)

if __name__ == '__main__':
    main()
