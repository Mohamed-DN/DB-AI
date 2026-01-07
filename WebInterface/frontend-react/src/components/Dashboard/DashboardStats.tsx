import { Database, Monitor, AlertTriangle, Server } from 'lucide-react';
import { useDashboardStats } from '../../hooks/useDatabases';

export default function DashboardStats() {
    const { data: stats, isLoading, error } = useDashboardStats();

    if (isLoading) {
        return (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="glass p-6 animate-pulse">
                        <div className="h-8 bg-gray-700 rounded w-16 mb-2"></div>
                        <div className="h-4 bg-gray-700 rounded w-24"></div>
                    </div>
                ))}
            </div>
        );
    }

    if (error) {
        return <div className="text-red-400">Error loading stats</div>;
    }

    const statCards = [
        {
            label: 'Total Databases',
            value: stats?.totalDatabases || 0,
            icon: Database,
            color: 'text-[--nexi-primary]',
            bgColor: 'bg-blue-500/10',
        },
        {
            label: 'Online',
            value: stats?.onlineCount || 0,
            icon: Monitor,
            color: 'text-emerald-400',
            bgColor: 'bg-emerald-500/10',
        },
        {
            label: 'Offline',
            value: stats?.offlineCount || 0,
            icon: Server,
            color: 'text-red-400',
            bgColor: 'bg-red-500/10',
        },
        {
            label: 'Warnings',
            value: stats?.warningCount || 0,
            icon: AlertTriangle,
            color: 'text-amber-400',
            bgColor: 'bg-amber-500/10',
        },
    ];

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {statCards.map((stat) => (
                <div
                    key={stat.label}
                    className={`glass p-6 hover:scale-105 transition-transform cursor-pointer ${stat.bgColor}`}
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <p className={`text-3xl font-bold ${stat.color}`}>{stat.value}</p>
                            <p className="text-gray-400 text-sm mt-1">{stat.label}</p>
                        </div>
                        <stat.icon className={`w-10 h-10 ${stat.color} opacity-60`} strokeWidth={1.5} />
                    </div>
                </div>
            ))}
        </div>
    );
}
