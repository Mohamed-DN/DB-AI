"""Pydantic models for inventory_databases collection"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class OSInfo(BaseModel):
    distro: str
    version: str
    kernel: Optional[str] = None


class CPUInfo(BaseModel):
    model: str
    architecture: str
    sockets: int
    cores_per_socket: int
    threads_total: int


class MemoryInfo(BaseModel):
    total_gb: int
    hugepages_configured: bool = False
    hugepages_size_gb: Optional[int] = None


class HostSpecs(BaseModel):
    os: OSInfo
    cpu: CPUInfo
    memory: MemoryInfo
    virtualization: Optional[dict] = None


class HostMetrics(BaseModel):
    collected_at: datetime
    load_avg_15m: float
    cpu_usage_pct: float
    ram_free_gb: float
    swap_used_pct: float


class Node(BaseModel):
    node_name: str
    hostname: str
    host_ip: str
    role: str
    status: str
    host_specs: Optional[HostSpecs] = None
    host_metrics: Optional[HostMetrics] = None


class Identity(BaseModel):
    db_unique_name: str
    db_name: str
    engine: str
    topology: str
    environment: str
    gateway_ref: str


class PDB(BaseModel):
    name: str
    open_mode: str


class OracleSpecific(BaseModel):
    architecture: Optional[str] = None
    grid_version: Optional[str] = None
    cluster_name: Optional[str] = None
    pdbs: List[PDB] = []


class Configuration(BaseModel):
    version: str
    port: int
    oracle_home: Optional[str] = None
    patches: List[str] = []
    oracle_specific: Optional[OracleSpecific] = None


class Licensing(BaseModel):
    product_edition: str
    support_identifier: Optional[str] = None
    active_options: List[str] = []


class Backup(BaseModel):
    tool: str
    last_full_backup: Optional[datetime] = None
    status: str


class Replication(BaseModel):
    is_active: bool
    technology: Optional[str] = None
    replication_mode: Optional[str] = None


class DataProtection(BaseModel):
    backup: Optional[Backup] = None
    replication: Optional[Replication] = None


class DiskGroup(BaseModel):
    name: str
    total_gb: int
    max_gb: Optional[int] = None
    used_pct: float
    alert_threshold_pct: int = 90
    state: str


class Tablespace(BaseModel):
    name: str
    used_pct: float
    autoextensible: str
    max_gb: Optional[int] = None
    alert_threshold_pct: int = 90


class Storage(BaseModel):
    last_check: Optional[datetime] = None
    asm_diskgroups: List[DiskGroup] = []
    tablespaces: List[Tablespace] = []


class DataRetention(BaseModel):
    enabled: bool = False
    retention_days: Optional[int] = None
    partition_manager: bool = False


class Policies(BaseModel):
    data_retention: Optional[DataRetention] = None


class InventoryDatabase(BaseModel):
    """Main model for inventory_databases collection"""
    identity: Identity
    nodes: List[Node] = []
    configuration: Optional[Configuration] = None
    licensing: Optional[Licensing] = None
    data_protection: Optional[DataProtection] = None
    storage: Optional[Storage] = None
    policies: Optional[Policies] = None

    class Config:
        populate_by_name = True
