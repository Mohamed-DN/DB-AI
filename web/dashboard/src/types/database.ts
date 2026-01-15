// Database types matching MongoDB schema

export interface Database {
    _id: string;
    identity: {
        db_unique_name: string;
        topology: 'PRIMARY' | 'REPLICA' | 'STANDALONE' | 'RAC' | 'PDB';
        engine: 'ORACLE' | 'POSTGRES';
        environment: string;
        host?: string;
        datacenter?: string;
        gateway_ref?: string;
        parent_cdb?: string;
    };
    connection: {
        container?: string;
        type: 'DOCKER' | 'REMOTE';
        host?: string;
        port?: number;
        service_name?: string;
        user?: string;
        password?: string;
    };
    state: {
        status: 'UP' | 'DOWN' | 'WARNING' | 'UNKNOWN' | 'MISSING';
        last_seen: string;
        metrics?: {
            hostname?: string;
            os_type?: string;
            cpu_count?: number;
            memory_gb?: number;
        };
    };
    configuration?: {
        version?: string;
        db_name?: string;
        open_mode?: string;
        log_mode?: string;
        oracle_specific?: {
            architecture?: string;
            cluster_name?: string;
            pdbs?: PDB[];
        };
    };
    pdbs?: PDB[];
}

export interface PDB {
    name: string;
    status: 'NORMAL' | 'READ WRITE' | 'MOUNTED' | string;
    open_mode?: string;
}

export interface Host {
    hostname: string;
    ip: string;
    os: string;
    databases: string[];
    cpu?: number;
    memory?: number;
    status: 'UP' | 'DOWN' | 'UNKNOWN';
}

export interface Alert {
    id: string;
    type: 'CRITICAL' | 'WARNING' | 'INFO';
    database: string;
    message: string;
    timestamp: string;
    resolved: boolean;
}

export interface DashboardStats {
    totalDatabases: number;
    onlineCount: number;
    offlineCount: number;
    warningCount: number;
    oracleCount: number;
    postgresCount: number;
}
