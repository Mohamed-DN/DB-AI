import axios from 'axios';
import type { Database } from '../types/database';

const API_BASE = '/api';  // Relative URL - Vite proxy routes to backend (8000 for V1, 9000 for V2)

const api = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Inventory
export const getDatabases = async (): Promise<Database[]> => {
    const { data } = await api.get('/inventory');
    return data || [];
};

// Alerts
export const getAlerts = async (): Promise<any[]> => {
    const { data } = await api.get('/alerts');
    return data || [];
};

// Dashboard Stats (computed from inventory + alerts)
export interface DashboardStats {
    totalDatabases: number;
    criticalAlerts: number;
    healthyAssets: number;
}

export const getDashboardStats = async (): Promise<DashboardStats> => {
    const [inventory, alerts] = await Promise.all([
        getDatabases(),
        getAlerts(),
    ]);

    return {
        totalDatabases: inventory.length,
        criticalAlerts: alerts.filter((a: any) => a.state === 'CRITICAL' && !a.processed).length,
        healthyAssets: inventory.filter((d: any) => d.state?.status === 'UP').length,
    };
};

// Delete database
export const deleteDatabase = async (dbName: string): Promise<void> => {
    await api.delete(`/inventory/${dbName}`);
};

// Refresh database
export const refreshDatabase = async (dbName: string): Promise<void> => {
    await api.post(`/action/refresh/${dbName}`);
};

// Connection
export const connectDatabase = async (
    dbName: string,
    mode: 'sql' | 'bash' | 'sysdba' = 'sql'
): Promise<{ status: string }> => {
    const { data } = await api.post(`/action/connect/${dbName}`, null, {
        params: { mode }
    });
    return data;
};

// AI Chat
export const sendChatMessage = async (message: string, model?: string): Promise<any> => {
    const payload = model ? { message, model } : { message };
    const { data } = await api.post('/chat', payload);
    return data;
};

// Auto-discovery
export const runAutoDiscovery = async (): Promise<void> => {
    await api.post('/action/scan');
};

// System status
export interface SystemStatus {
    status: string;
    paused: boolean;
}

export const getSystemStatus = async (): Promise<SystemStatus> => {
    const { data } = await api.get('/system/status');
    const status = data?.status || (data?.paused ? 'PAUSED' : 'RUNNING');
    const paused = data?.paused ?? status === 'PAUSED';
    return { status, paused };
};

export const setSystemStatus = async (paused: boolean): Promise<void> => {
    await api.post('/system/status', { status: paused ? 'PAUSED' : 'RUNNING' });
};

// Emails
export const getEmails = async (): Promise<any[]> => {
    const { data } = await api.get('/emails');
    return data || [];
};

// Raw collection for Explorer - use /raw/{collection}
export const getRawCollection = async (collection: string): Promise<any[]> => {
    try {
        const { data } = await api.get(`/raw/${collection}`);
        return data || [];
    } catch (error) {
        console.error(`Failed to fetch collection ${collection}:`, error);
        return [];
    }
};

// Agents - mock status since backend may not have endpoint
export const getAgentsStatus = async (): Promise<any> => {
    try {
        const { data } = await api.get('/agents/status');
        return data;
    } catch (error) {
        // Return mock data if endpoint doesn't exist
        return {
            agents: {
                scout: { running: false, script: '' },
                collector: { running: false, script: '' },
                watcher: { running: false, script: '' },
                criticalalert: { running: false, script: '' },
                forensicanalyzer: { running: false, script: '' },
                checkmk_bridge: { running: false, script: '' }
            }
        };
    }
};

export const startAgent = async (agentName: string): Promise<any> => {
    try {
        const { data } = await api.post(`/agents/start/${agentName}`);
        return data;
    } catch (error) {
        console.error(`Failed to start agent ${agentName}:`, error);
        return { error: 'Failed to start agent' };
    }
};

// LLM
export const getCurrentModel = async (): Promise<any> => {
    const { data } = await api.get('/llm/current');
    return data;
};

export const getLlmConfig = async (): Promise<any> => {
    const { data } = await api.get('/llm/config');
    return data;
};

export const switchModel = async (model: string): Promise<void> => {
    await api.post('/llm/switch', { model });
};

// GPU
export const getGpuStatus = async (): Promise<any> => {
    const { data } = await api.get('/gpu/status');
    return data;
};

// Metrics
export interface MetricsResponse {
    summary: {
        buffer_hit: number;
        tps: number;
        storage_gb: number;
        total_connections: number;
        avg_query_ms: number;
        active_alerts: number;
    };
    connections_by_db: Array<{
        name: string;
        active: number;
        idle: number;
        engine: string;
    }>;
    pg_databases: Array<{
        name: string;
        size_gb: number;
        connections: number;
    }>;
    oracle_tablespaces: Array<{
        name: string;
        used_pct: number;
        used_gb: number;
        max_gb: number;
    }>;
    database_count: number;
}

export const getMetrics = async (dbFilter?: string): Promise<MetricsResponse> => {
    const params = dbFilter && dbFilter !== 'all' ? { db: dbFilter } : {};
    const { data } = await api.get('/metrics', { params });
    return data;
};

export const getDeepMetrics = async (): Promise<any> => {
    const { data } = await api.get('/metrics/deep');
    return data;
};
