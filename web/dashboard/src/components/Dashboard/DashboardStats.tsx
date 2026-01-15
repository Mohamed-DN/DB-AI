import { Database, AlertTriangle, HeartPulse } from 'lucide-react';
import { useDashboardStats } from '../../hooks/useDatabases';

export default function DashboardStats() {
    const { data: stats, isLoading, error } = useDashboardStats();

    if (error) {
        return (
            <div className="grid grid-cols-3 gap-6">
                {[1, 2, 3].map(i => (
                    <div key={i} className="glass p-6 text-center">
                        <div className="text-red-400 text-2xl">--</div>
                        <div className="text-gray-500 text-sm mt-2">Error loading</div>
                    </div>
                ))}
            </div>
        );
    }

    const statCards = [
        {
            label: 'TOTAL DATABASES',
            value: isLoading ? '--' : stats?.totalDatabases ?? 0,
            icon: Database,
            gradient: 'from-blue-500/20 to-cyan-500/20',
            iconColor: 'text-blue-400',
        },
        {
            label: 'CRITICAL ALERTS',
            value: isLoading ? '--' : stats?.criticalAlerts ?? 0,
            icon: AlertTriangle,
            gradient: 'from-red-500/20 to-orange-500/20',
            iconColor: 'text-red-400',
        },
        {
            label: 'HEALTHY ASSETS',
            value: isLoading ? '--' : stats?.healthyAssets ?? 0,
            icon: HeartPulse,
            gradient: 'from-emerald-500/20 to-green-500/20',
            iconColor: 'text-emerald-400',
        },
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {statCards.map((stat) => (
                <div
                    key={stat.label}
                    className={`glass p-8 text-center bg-gradient-to-br ${stat.gradient} hover:scale-[1.02] transition-transform cursor-pointer`}
                >
                    <div className={`text-4xl font-bold ${stat.iconColor}`}>
                        {stat.value}
                    </div>
                    <div className="text-gray-400 text-sm mt-3 uppercase tracking-wider">
                        {stat.label}
                    </div>
                </div>
            ))}
        </div>
    );
}
