import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../services/api';
import type { Database, DashboardStats } from '../types/database';

// Dashboard stats hook
export function useDashboardStats() {
    return useQuery<DashboardStats>({
        queryKey: ['dashboardStats'],
        queryFn: api.getDashboardStats,
        refetchInterval: 30000, // Refresh every 30 seconds
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

// Refresh database mutation
export function useRefreshDatabase() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: api.refreshDatabase,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['databases'] });
        },
    });
}

// Connect to database
export function useConnectDatabase() {
    return useMutation({
        mutationFn: ({ dbName, mode }: { dbName: string; mode: 'sql' | 'bash' }) =>
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
