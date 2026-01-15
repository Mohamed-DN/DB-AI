"""
System Information Extractor
Extracts OS, CPU, Memory information from Linux hosts.
"""
from typing import Dict, Optional


class SystemExtractor:
    """Extract system information via shell commands"""

    # Commands for system info
    CMD_OS_RELEASE = "cat /etc/os-release"
    CMD_KERNEL = "uname -r"
    CMD_CPU_INFO = "lscpu"
    CMD_MEMORY = "free -g"
    CMD_HOSTNAME = "hostname -f"
    CMD_IP_ADDRESS = "hostname -I | awk '{print $1}'"

    @staticmethod
    def parse_os_release(output: str) -> Dict:
        """Parse /etc/os-release"""
        result = {}
        for line in output.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                result[key] = value.strip('"')
        return {
            "distro": result.get("NAME", "Unknown"),
            "version": result.get("VERSION_ID", "Unknown"),
        }

    @staticmethod
    def parse_lscpu(output: str) -> Dict:
        """Parse lscpu output"""
        result = {}
        for line in output.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
        
        return {
            "model": result.get("Model name", "Unknown"),
            "architecture": result.get("Architecture", "x86_64"),
            "sockets": int(result.get("Socket(s)", 1)),
            "cores_per_socket": int(result.get("Core(s) per socket", 1)),
            "threads_total": int(result.get("CPU(s)", 1)),
        }

    @staticmethod
    def parse_free(output: str) -> Dict:
        """Parse free -g output"""
        lines = output.strip().split('\n')
        if len(lines) >= 2:
            # Mem: total used free shared buff/cache available
            parts = lines[1].split()
            if len(parts) >= 4:
                return {
                    "total_gb": int(parts[1]),
                    "used_gb": int(parts[2]),
                    "free_gb": int(parts[3]),
                }
        return {"total_gb": 0, "used_gb": 0, "free_gb": 0}


class SystemDataCollector:
    """Collects system data from remote host"""

    def __init__(self, ssh_executor):
        self.executor = ssh_executor

    def collect_all(self) -> Dict:
        """Collect all system info"""
        # Get each piece of info
        os_release, _, _ = self.executor(SystemExtractor.CMD_OS_RELEASE)
        kernel, _, _ = self.executor(SystemExtractor.CMD_KERNEL)
        cpu_info, _, _ = self.executor(SystemExtractor.CMD_CPU_INFO)
        memory, _, _ = self.executor(SystemExtractor.CMD_MEMORY)
        hostname, _, _ = self.executor(SystemExtractor.CMD_HOSTNAME)
        ip_addr, _, _ = self.executor(SystemExtractor.CMD_IP_ADDRESS)

        os_data = SystemExtractor.parse_os_release(os_release)
        os_data["kernel"] = kernel.strip()

        return {
            "hostname": hostname.strip(),
            "host_ip": ip_addr.strip(),
            "os": os_data,
            "cpu": SystemExtractor.parse_lscpu(cpu_info),
            "memory": SystemExtractor.parse_free(memory),
        }
