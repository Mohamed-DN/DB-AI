import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Database, ShieldCheck, Trash2, RefreshCw, AlertTriangle, CheckCircle, Server, Clock } from 'lucide-react';
import AddInstanceModal from './AddInstanceModal';

interface OEMInstance {
    name: string;
    url: string;
    username: string;
    is_connected: boolean;
    last_check?: string;
}

interface OEMTarget {
    name: string;
    engine: string;
    status: string;
    host?: string;
    port?: number;
    metrics: Record<string, number>;
    last_collected?: string;
}

export default function OEMDashboard() {
    const [showAddModal, setShowAddModal] = useState(false);
    const queryClient = useQueryClient();

    // Fetch Instances
    const { data: instances } = useQuery<OEMInstance[]>({
        queryKey: ['oem-instances'],
        queryFn: async () => {
            const res = await fetch('/api/oem/instances');
            if (!res.ok) throw new Error('Failed to fetch instances');
            return res.json();
        }
    });

    // Fetch Targets
    const { data: targets, isLoading: isLoadingTargets } = useQuery<OEMTarget[]>({
        queryKey: ['oem-targets'],
        queryFn: async () => {
            const res = await fetch('/api/oem/targets');
            if (!res.ok) throw new Error('Failed to fetch targets');
            return res.json();
        }
    });

    // Delete Instance Mutation
    const deleteInstance = useMutation({
        mutationFn: async (name: string) => {
            const res = await fetch(`/ api / oem / instances / ${name} `, { method: 'DELETE' });
            if (!res.ok) throw new Error('Failed to delete instance');
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['oem-instances'] });
        }
    });

    // Manual Collection Trigger
    const collectMetrics = useMutation({
        mutationFn: async () => {
            const res = await fetch('/api/oem/collect', { method: 'POST' });
            if (!res.ok) throw new Error('Collection failed');
            return res.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['oem-targets'] });
        }
    });

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <AddInstanceModal
                isOpen={showAddModal}
                onClose={() => setShowAddModal(false)}
                onSuccess={() => queryClient.invalidateQueries({ queryKey: ['oem-instances'] })}
            />

            {/* Header */}
            <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                            <ShieldCheck className="w-8 h-8 text-purple-500" />
                            OEM Dashboard
                        </h1>
                        <p className="text-gray-400 mt-1">
                            Oracle Enterprise Manager Integration & Metrics
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={() => collectMetrics.mutate()}
                            disabled={collectMetrics.isPending}
                            className="btn-secondary flex items-center gap-2"
                        >
                            <RefreshCw className={`w - 4 h - 4 ${collectMetrics.isPending ? 'animate-spin' : ''} `} />
                            Sync Now
                        </button>
                        <button
                            onClick={() => setShowAddModal(true)}
                            className="btn-primary flex items-center gap-2 bg-purple-600 hover:bg-purple-500"
                        >
                            <Plus className="w-4 h-4" />
                            Add Instance
                        </button>
                    </div>
                </div>
            </div>

            {/* Instances Grid */}
            <section>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Server className="w-5 h-5 text-gray-400" />
                    Connected OEM Instances
                </h3>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {instances?.map((inst) => (
                        <div key={inst.name} className="glass p-5 rounded-xl border border-gray-800 hover:border-purple-500/30 transition-all group relative">
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                                        <ShieldCheck className="w-6 h-6" />
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-white">{inst.name}</h4>
                                        <div className="flex items-center gap-2 text-xs">
                                            <span className={`w - 2 h - 2 rounded - full ${inst.is_connected ? 'bg-green-500' : 'bg-red-500'} `}></span>
                                            <span className="text-gray-400">{inst.is_connected ? 'Connected' : 'Disconnected'}</span>
                                        </div>
                                    </div>
                                </div>
                                <button
                                    onClick={() => {
                                        if (confirm(`Delete instance ${inst.name}?`)) deleteInstance.mutate(inst.name);
                                    }}
                                    className="p-2 hover:bg-red-500/20 rounded-lg text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                            <div className="text-xs text-gray-500 font-mono bg-gray-900/50 p-2 rounded truncate">
                                {inst.url}
                            </div>
                        </div>
                    ))}
                    {instances?.length === 0 && (
                        <div className="col-span-full py-8 text-center border-2 border-dashed border-gray-800 rounded-xl">
                            <ShieldCheck className="w-10 h-10 text-gray-600 mx-auto mb-3" />
                            <p className="text-gray-400">No OEM instances configured</p>
                            <button onClick={() => setShowAddModal(true)} className="text-purple-400 hover:text-purple-300 text-sm mt-2">
                                + Connect your first instance
                            </button>
                        </div>
                    )}
                </div>
            </section>

            {/* Targets / Metrics Section */}
            <section>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Database className="w-5 h-5 text-gray-400" />
                    Discovered Oracle Databases
                </h3>

                {isLoadingTargets ? (
                    <div className="text-center py-12">
                        <Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto" />
                        <p className="text-gray-500 mt-2">Loading metrics...</p>
                    </div>
                ) : (
                    <div className="grid gap-4">
                        {targets?.map((target) => (
                            <div key={target.name} className="glass p-6 rounded-xl border border-gray-800 flex flex-col md:flex-row gap-6 items-start md:items-center justify-between">
                                {/* Identity */}
                                <div className="flex items-center gap-4 min-w-[200px]">
                                    <div className="p-3 rounded-full bg-orange-500/10 text-orange-500">
                                        <Database className="w-6 h-6" />
                                    </div>
                                    <div>
                                        <h4 className="text-lg font-bold text-white">{target.name}</h4>
                                        <div className="text-sm text-gray-400 flex items-center gap-2">
                                            <span className="px-2 py-0.5 rounded bg-gray-800 text-xs">{target.engine}</span>
                                            {target.host && <span>• {target.host}</span>}
                                        </div>
                                    </div>
                                </div>

                                {/* Status */}
                                <div className="flex flex-col gap-1">
                                    <div className="text-xs text-gray-500 uppercase font-semibold">Status</div>
                                    <div className="flex items-center gap-2">
                                        {target.status === 'UP' || target.status === 'OPEN' ? (
                                            <CheckCircle className="w-4 h-4 text-green-500" />
                                        ) : (
                                            <AlertTriangle className="w-4 h-4 text-red-500" />
                                        )}
                                        <span className={target.status === 'UP' || target.status === 'OPEN' ? 'text-green-400' : 'text-red-400'}>
                                            {target.status || 'UNKNOWN'}
                                        </span>
                                    </div>
                                </div>

                                {/* Metrics */}
                                <div className="flex gap-8 flex-1 justify-end">
                                    <MetricItem
                                        label="CPU Usage"
                                        value={target.metrics?.cpu_usage_percent}
                                        unit="%"
                                        color="blue"
                                    />
                                    <MetricItem
                                        label="Memory"
                                        value={target.metrics?.memory_usage_percent}
                                        unit="%"
                                        color="purple"
                                    />
                                    <MetricItem
                                        label="Sessions"
                                        value={target.metrics?.active_sessions}
                                        unit=""
                                        color="emerald"
                                    />
                                </div>

                                {/* Last Update */}
                                <div className="text-right text-xs text-gray-500 min-w-[120px]">
                                    <div className="flex items-center justify-end gap-1 mb-1">
                                        <Clock className="w-3 h-3" /> Last Updated
                                    </div>
                                    {target.last_collected ? new Date(target.last_collected).toLocaleTimeString() : 'Never'}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
}

function MetricItem({ label, value, unit, color }: { label: string, value?: number, unit: string, color: string }) {
    if (value === undefined) return (
        <div className="opacity-50">
            <div className="text-xs text-gray-500">{label}</div>
            <div className="text-lg font-bold text-gray-600">-</div>
        </div>
    );

    return (
        <div>
            <div className="text-xs text-gray-400 mb-0.5">{label}</div>
            <div className={`text - xl font - bold text - ${color} -400`}>
                {value.toFixed(1)}<span className="text-sm text-gray-600 ml-0.5">{unit}</span>
            </div>
        </div>
    );
}

// Utility component (only used here)
function Loader2({ className }: { className?: string }) {
    return <RefreshCw className={className} />;
}
