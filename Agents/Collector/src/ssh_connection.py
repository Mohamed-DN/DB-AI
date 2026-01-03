"""
SSH Gateway Connection Helper
Provides tunneled connections to target hosts via bastion/jump host.
"""
import os
from typing import Optional, Tuple
import paramiko
from dotenv import load_dotenv

load_dotenv()


class GatewayConnection:
    """SSH connection through gateway/bastion host"""

    def __init__(
        self,
        gateway_host: str = None,
        gateway_port: int = 22,
        gateway_user: str = None,
        key_file: str = None,
        password: str = None
    ):
        self.gateway_host = gateway_host or os.getenv("GATEWAY_HOST")
        self.gateway_port = gateway_port
        self.gateway_user = gateway_user or os.getenv("GATEWAY_USER")
        self.key_file = key_file or os.getenv("GATEWAY_KEY_FILE")
        self.password = password or os.getenv("GATEWAY_PASSWORD")
        
        self._gateway_client: Optional[paramiko.SSHClient] = None
        self._target_client: Optional[paramiko.SSHClient] = None

    def connect_gateway(self) -> paramiko.SSHClient:
        """Connect to the gateway/bastion host"""
        if self._gateway_client is None:
            self._gateway_client = paramiko.SSHClient()
            self._gateway_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_params = {
                "hostname": self.gateway_host,
                "port": self.gateway_port,
                "username": self.gateway_user,
            }
            
            if self.key_file and os.path.exists(self.key_file):
                connect_params["key_filename"] = self.key_file
            elif self.password:
                connect_params["password"] = self.password
            
            self._gateway_client.connect(**connect_params)
        
        return self._gateway_client

    def connect_target(self, target_host: str, target_port: int = 22, target_user: str = None) -> paramiko.SSHClient:
        """Connect to target host through gateway"""
        gateway = self.connect_gateway()
        
        # Create tunnel through gateway
        transport = gateway.get_transport()
        dest_addr = (target_host, target_port)
        local_addr = ("localhost", 0)
        channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)
        
        # Connect to target through tunnel
        target_client = paramiko.SSHClient()
        target_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        target_client.connect(
            hostname=target_host,
            port=target_port,
            username=target_user or self.gateway_user,
            sock=channel,
            key_filename=self.key_file if self.key_file else None,
            password=self.password if not self.key_file else None
        )
        
        return target_client

    def execute_on_target(self, target_host: str, command: str, target_user: str = None) -> Tuple[str, str, int]:
        """Execute command on target host through gateway"""
        client = self.connect_target(target_host, target_user=target_user)
        try:
            stdin, stdout, stderr = client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            return stdout.read().decode(), stderr.read().decode(), exit_code
        finally:
            client.close()

    def close(self):
        """Close all connections"""
        if self._target_client:
            self._target_client.close()
            self._target_client = None
        if self._gateway_client:
            self._gateway_client.close()
            self._gateway_client = None


class DirectConnection:
    """Direct SSH connection (no gateway)"""

    def __init__(self, host: str, user: str, key_file: str = None, password: str = None):
        self.host = host
        self.user = user
        self.key_file = key_file
        self.password = password
        self._client: Optional[paramiko.SSHClient] = None

    def connect(self) -> paramiko.SSHClient:
        """Connect directly to host"""
        if self._client is None:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_params = {"hostname": self.host, "username": self.user}
            if self.key_file:
                connect_params["key_filename"] = self.key_file
            elif self.password:
                connect_params["password"] = self.password
            
            self._client.connect(**connect_params)
        
        return self._client

    def execute(self, command: str) -> Tuple[str, str, int]:
        """Execute command on host"""
        client = self.connect()
        stdin, stdout, stderr = client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        return stdout.read().decode(), stderr.read().decode(), exit_code

    def close(self):
        """Close connection"""
        if self._client:
            self._client.close()
            self._client = None
