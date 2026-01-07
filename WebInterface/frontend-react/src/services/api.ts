import axios from 'axios';
import type { Database } from '../types/database';

const API_BASE = 'http://localhost:8000/api';

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
    mode: 'sql' | 'bash' = 'sql'
): Promise<{ status: string }> => {
    const { data } = await api.post(`/action/connect/${dbName}`, null, {
        params: { mode }
    });
    return data;
};

// AI Chat
export const sendChatMessage = async (message: string): Promise<any> => {
    const { data } = await api.post('/chat', { message });
    return data;
};

// Auto-discovery
export const runAutoDiscovery = async (): Promise<void> => {
    await api.post('/action/auto-discovery');
};

// System status
export const getSystemStatus = async (): Promise<{ paused: boolean }> => {
    const { data } = await api.get('/system/status');
    return data;
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
            scout: { running: false },
            collector: { running: false },
            watcher: { running: false },
            criticalalert: { running: false },
            forensicanalyzer: { running: false },
            checkmk_bridge: { running: false }
        };
    }
};

export const startAgent = async (agentName: string): Promise<any> => {
    try {
        const { data } = await api.post(`/agents/${agentName}/start`);
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

export const switchModel = async (model: string): Promise<void> => {
    await api.post('/llm/switch', { model });
};

// GPU
export const getGpuStatus = async (): Promise<any> => {
    const { data } = await api.get('/gpu/status');
    return data;
};
