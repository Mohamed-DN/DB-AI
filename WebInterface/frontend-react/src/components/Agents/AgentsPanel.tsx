import { Bot, Play, CheckCircle, XCircle, Loader } from 'lucide-react';
import { useAgentsStatus } from '../../hooks/useDatabases';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../../services/api';

const AGENTS = [
    { id: 'scout', name: 'Scout Agent', description: 'Scans for new databases' },
    { id: 'collector', name: 'Collector', description: 'Collects database metrics' },
    { id: 'watcher', name: 'Watcher', description: 'Monitors container health' },
    { id: 'criticalalert', name: 'Critical Alert', description: 'Processes critical alerts' },
    { id: 'forensicanalyzer', name: 'Forensic AI', description: 'AI-powered alert analysis' },
    { id: 'checkmk_bridge', name: 'CheckMK Bridge', description: 'Syncs with CheckMK' },
];

export default function AgentsPanel() {
    const { data: agentsStatus, isLoading } = useAgentsStatus();
    const queryClient = useQueryClient();

    const startAgentMutation = useMutation({
        mutationFn: api.startAgent,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['agentsStatus'] });
        },
    });

    const getAgentStatus = (agentId: string) => {
        if (!agentsStatus) return 'unknown';
        const status = (agentsStatus as Record<string, { running?: boolean }>)[agentId];
        return status?.running ? 'running' : 'stopped';
    };

    if (isLoading) {
        return <div className="glass p-8 text-center text-gray-500">Loading agents...</div>;
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {AGENTS.map((agent) => {
                const status = getAgentStatus(agent.id);
                return (
                    <div key={agent.id} className="glass p-6">
                        <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${status === 'running' ? 'bg-green-500/20' : 'bg-gray-500/20'}`}>
                                    <Bot className={`w-5 h-5 ${status === 'running' ? 'text-green-400' : 'text-gray-400'}`} />
                                </div>
                                <div>
                                    <h4 className="font-semibold">{agent.name}</h4>
                                    <p className="text-xs text-gray-500">{agent.description}</p>
                                </div>
                            </div>
                            {status === 'running' ? (
                                <CheckCircle className="w-5 h-5 text-green-400" />
                            ) : (
                                <XCircle className="w-5 h-5 text-gray-500" />
                            )}
                        </div>

                        <div className="flex items-center justify-between">
                            <span className={`text-xs px-2 py-1 rounded ${status === 'running' ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                                {status.toUpperCase()}
                            </span>
                            <button
                                onClick={() => startAgentMutation.mutate(agent.id)}
                                disabled={startAgentMutation.isPending}
                                className="btn-secondary text-sm"
                            >
                                {startAgentMutation.isPending ? (
                                    <Loader className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Play className="w-4 h-4" />
                                )}
                                Run Once
                            </button>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
