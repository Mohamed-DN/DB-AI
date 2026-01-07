import axios from 'axios';
import type { Database, DashboardStats } from '../types/database';

const API_BASE = '/api';

const api = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Dashboard
export const getDashboardStats = async (): Promise<DashboardStats> => {
    const { data } = await api.get('/dashboard');
    return data;
};

// Inventory
export const getDatabases = async (): Promise<Database[]> => {
    const { data } = await api.get('/inventory');
    return data;
};

export const deleteDatabase = async (dbName: string): Promise<void> => {
    await api.delete(`/inventory/${dbName}`);
};

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

// AI Chat (LangChain)
export const sendChatMessage = async (message: string): Promise<{ response: string }> => {
    const { data } = await api.post('/ai/chat', { message });
    return data;
};

// Alerts
export const getAlerts = async (): Promise<any[]> => {
    const { data } = await api.get('/alerts');
    return data;
};

// Auto-discovery
export const runAutoDiscovery = async (): Promise<void> => {
    await api.post('/action/auto-discovery');
};

// Pause/Resume system
export const pauseSystem = async (): Promise<void> => {
    await api.post('/system/pause');
};

export const resumeSystem = async (): Promise<void> => {
    await api.post('/system/resume');
};
