import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useAlerts } from '../../hooks/useDatabases';

export default function AlertsPanel() {
    const { data: alerts, isLoading, refetch } = useAlerts();

    if (isLoading) {
        return <div className="glass p-8 text-center text-gray-500">Loading alerts...</div>;
    }

    return (
        <div>
            <div className="flex justify-end mb-4">
                <button onClick={() => refetch()} className="btn-primary text-sm">
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                </button>
            </div>

            <div className="space-y-3">
                {alerts && alerts.length > 0 ? (
                    alerts.map((alert: any, index: number) => (
                        <div
                            key={alert._id || index}
                            className={`glass p-4 border-l-4 ${alert.state === 'CRITICAL'
                                    ? 'border-l-red-500 bg-red-500/10'
                                    : alert.state === 'WARNING'
                                        ? 'border-l-yellow-500 bg-yellow-500/10'
                                        : 'border-l-blue-500 bg-blue-500/10'
                                }`}
                        >
                            <div className="flex justify-between items-start">
                                <div>
                                    <h4 className="font-semibold flex items-center gap-2">
                                        <AlertTriangle
                                            className={`w-4 h-4 ${alert.state === 'CRITICAL' ? 'text-red-400' : 'text-yellow-400'
                                                }`}
                                        />
                                        {alert.message}
                                    </h4>
                                    <p className="text-gray-400 text-sm mt-1">
                                        {alert.service} on {alert.host_name}
                                    </p>
                                </div>
                                <span className="text-gray-500 text-xs">
                                    {alert.timestamp
                                        ? new Date(alert.timestamp).toLocaleTimeString()
                                        : 'N/A'}
                                </span>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="glass p-12 text-center">
                        <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-gray-600" strokeWidth={1} />
                        <p className="text-gray-500">No alerts at this time</p>
                    </div>
                )}
            </div>
        </div>
    );
}
