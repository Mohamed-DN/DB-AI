import { useState } from 'react';
import { Database, Activity, AlertTriangle } from 'lucide-react';

export function MonitoringDashboard() {
    const [activeView, setActiveView] = useState<'grafana' | 'checkmk'>('grafana');

    const grafanaUrl = "http://localhost:3003/d/nexi-dba-v2/nexi-db-checkmk-and-critical-events-v2?orgId=1&refresh=5s&kiosk"; // Kiosk mode for full screen
    const checkmkUrl = "http://localhost:8080/nexi_monitor/check_mk/index.py?start_url=%2Fnexi_monitor%2Fcheck_mk%2Fview.py%3Fview_name%3Dallhosts"; // Direct to hosts view

    const [userRole, setUserRole] = useState<'admin' | 'dev' | 'viewer'>('admin');

    return (
        <div className="space-y-6">
            {/* Role & Quick Actions Header */}
            <div className="flex items-center justify-between gap-4 glass p-4 rounded-xl">
                <div className="flex items-center gap-4">
                    <h2 className="text-xl font-bold text-white">Monitoring Hub</h2>
                    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700">
                        <span className="text-xs text-slate-400">View as:</span>
                        <select
                            value={userRole}
                            onChange={(e) => setUserRole(e.target.value as any)}
                            className="bg-transparent text-sm font-medium text-blue-400 focus:outline-none"
                        >
                            <option value="admin">Admin</option>
                            <option value="dev">Developer</option>
                            <option value="viewer">Viewer</option>
                        </select>
                    </div>
                </div>

                <div className="flex gap-2">
                    {/* Direct Links requested by user */}
                    <a
                        href="http://localhost:3003"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-600 to-red-600 rounded-lg font-medium text-white hover:opacity-90 transition-all shadow-lg shadow-orange-500/20"
                    >
                        <Database className="w-4 h-4" />
                        Open Grafana
                    </a>
                    <a
                        href="http://localhost:8080/nexi_monitor"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg font-medium text-white hover:opacity-90 transition-all shadow-lg shadow-green-500/20"
                    >
                        <Activity className="w-4 h-4" />
                        Open CheckMK
                    </a>
                    <a
                        href="http://localhost:3001"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg font-medium text-white hover:opacity-90 transition-all shadow-lg shadow-purple-500/20"
                    >
                        <Activity className="w-4 h-4" />
                        Open Langfuse
                    </a>
                </div>
            </div>

            <div className="flex items-center justify-between gap-4">
                <div className="flex gap-2">
                    <button
                        onClick={() => setActiveView('grafana')}
                        className={`px-4 py-2 rounded-lg font-medium transition-colors ${activeView === 'grafana'
                            ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                            }`}
                    >
                        Grafana Dashboard
                    </button>
                    <button
                        onClick={() => setActiveView('checkmk')}
                        className={`px-4 py-2 rounded-lg font-medium transition-colors ${activeView === 'checkmk'
                            ? 'bg-amber-600 text-white shadow-lg shadow-amber-500/30'
                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                            }`}
                    >
                        CheckMK Console
                    </button>
                </div>

                {userRole === 'admin' && (
                    <span className="text-xs text-slate-500 flex items-center gap-1">
                        <AlertTriangle size={12} />
                        Admin Controls Enabled
                    </span>
                )}
            </div>

            <div className="glass rounded-xl overflow-hidden h-[800px] border border-slate-700/50 relative">
                <iframe
                    src={activeView === 'grafana' ? grafanaUrl : checkmkUrl}
                    title="Monitoring Dashboard"
                    className="w-full h-full border-0 bg-white"
                />

                {/* Helper overlay for first load or auth issues */}
                {activeView === 'grafana' && (
                    <div className="absolute bottom-4 right-4 bg-slate-900/90 p-4 rounded-lg text-xs text-slate-400 max-w-xs">
                        Configured for Grafana on port 3003. <br />
                        Default user: admin / NexiGrafana2024!
                    </div>
                )}
            </div>
        </div>
    );
}
