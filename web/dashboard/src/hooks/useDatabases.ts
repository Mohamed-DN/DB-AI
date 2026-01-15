import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../services/api';
import type { Database } from '../types/database';

// Dashboard stats hook
export function useDashboardStats() {
    return useQuery({
        queryKey: ['dashboardStats'],
        queryFn: api.getDashboardStats,
        refetchInterval: 30000,
    });
}

// Databases list hook
export function useDatabases() {
    return useQuery<Database[]>({
        queryKey: ['databases'],
        queryFn: api.getDatabases,
        refetchInterval: 30000,
    });
}

// Alerts hook
export function useAlerts() {
    return useQuery({
        queryKey: ['alerts'],
        queryFn: api.getAlerts,
        refetchInterval: 30000,
    });
}

// Delete database mutation
export function useDeleteDatabase() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: api.deleteDatabase,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['databases'] });
            queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
        },
    });
}

// Connect to database
export function useConnectDatabase() {
    return useMutation({
        mutationFn: ({ dbName, mode }: { dbName: string; mode: 'sql' | 'bash' | 'sysdba' }) =>
            api.connectDatabase(dbName, mode),
    });
}

// Auto-discovery
export function useAutoDiscovery() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: api.runAutoDiscovery,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['databases'] });
            queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
        },
    });
}

// System status
export function useSystemStatus() {
    return useQuery({
        queryKey: ['systemStatus'],
        queryFn: api.getSystemStatus,
        refetchInterval: 10000,
    });
}

export function useSetSystemStatus() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: api.setSystemStatus,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['systemStatus'] });
        },
    });
}

// Emails
export function useEmails() {
    return useQuery({
        queryKey: ['emails'],
        queryFn: api.getEmails,
    });
}

// Agents
export function useAgentsStatus() {
    return useQuery({
        queryKey: ['agentsStatus'],
        queryFn: api.getAgentsStatus,
        refetchInterval: 10000,
    });
}

// LLM
export function useCurrentModel() {
    return useQuery({
        queryKey: ['currentModel'],
        queryFn: api.getCurrentModel,
    });
}

// GPU
export function useGpuStatus() {
    return useQuery({
        queryKey: ['gpuStatus'],
        queryFn: api.getGpuStatus,
        refetchInterval: 5000,
    });
}
