

import { Bot, Play, CheckCircle, XCircle, Loader, Terminal as TerminalIcon, Brain, RefreshCw, Eye } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useState } from 'react';

const API_BASE = 'http://localhost:8000/api';

// --- Types ---
interface AgentInfo {
    script: string;
    running: boolean;
}

interface AgentsStatus {
    agents: Record<string, AgentInfo>;
}

interface RagStatus {
    ollama: { connected: boolean; models: string[] };
    qdrant: { connected: boolean; collections: number };
}

interface ProcessResult {
    status: string;
    agent: string;
    exit_code?: number;
    output: string[];
    success: boolean;
}

// --- API ---
const getAgentsStatus = async (): Promise<AgentsStatus> => {
    const { data } = await axios.get(`${API_BASE}/agents/status`);
    return data;
};

const getRagStatus = async (): Promise<RagStatus> => {
    const { data } = await axios.get(`${API_BASE}/rag/status`);
    return data;
};

const startAgent = async (name: string): Promise<ProcessResult> => {
    const { data } = await axios.post(`${API_BASE}/agents/start/${name}`);
    return data;
};

const triggerAction = async (action: string) => {
    const { data } = await axios.post(`${API_BASE}/agents/trigger/${action}`);
    return data;
};

// --- Parsed Agent List for UI ---
// Map backend keys to nice UI
const AGENT_UI: Record<string, { label: string; desc: string; icon: any }> = {
    Scout: { label: 'Scout Agent', desc: 'Auto-Discovery', icon: <Bot className="w-5 h-5 text-purple-400" /> },
    Collector: { label: 'Metric Collector', desc: 'Database Telemetry', icon: <RefreshCw className="w-5 h-5 text-blue-400" /> },
    Watcher: { label: 'Log Watcher', desc: 'Live Log Monitoring', icon: <Eye className="w-5 h-5 text-yellow-400" /> },
    CriticalAlert: { label: 'Critical Aleter', desc: 'Alert Processing', icon: <TerminalIcon className="w-5 h-5 text-red-400" /> },
    ForensicAnalyzer: { label: 'Forensic AI', desc: 'AI Root Cause Analysis', icon: <Brain className="w-5 h-5 text-pink-400" /> },
    CheckMK_Bridge: { label: 'CheckMK Bridge', desc: 'Sync with CheckMK', icon: <CheckCircle className="w-5 h-5 text-green-400" /> },
};

export default function AgentsPanel() {
    const queryClient = useQueryClient();
    const [logVisible, setLogVisible] = useState(false);
    const [logs, setLogs] = useState<ProcessResult | null>(null);

    // Queries
    const agentsQuery = useQuery({ queryKey: ['agentsStatus'], queryFn: getAgentsStatus, refetchInterval: 5000 });
    const ragQuery = useQuery({ queryKey: ['ragStatus'], queryFn: getRagStatus, refetchInterval: 10000 });

    // Mutations
    const startMutation = useMutation({
        mutationFn: startAgent,
        onMutate: () => setLogVisible(true), // Open modal immediately
        onSuccess: (data) => {
            setLogs(data);
            queryClient.invalidateQueries({ queryKey: ['agentsStatus'] });
        },
        onError: (error: any) => {
            setLogs({
                status: 'error',
                agent: 'Unknown',
                success: false,
                output: ['Error: ' + (error.response?.data?.detail || error.message)]
            });
        }
    });

    const triggerMutation = useMutation({
        mutationFn: triggerAction,
        onSuccess: (data) => {
            alert(data.status); // Simple feedback for triggers
        },
    });

    // Helper to get UI info
    const getAgentUI = (key: string) => AGENT_UI[key] || { label: key, desc: 'Agent Script', icon: <Bot className="w-5 h-5" /> };

    return (
        <div className="space-y-6">
            {/* RAG Status Header */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="glass p-4 flex items-center justify-between">
                    <div>
                        <div className="text-sm text-gray-400">Ollama LLM</div>
                        <div className="text-lg font-bold flex items-center gap-2">
                            {ragQuery.data?.ollama.connected ? (
                                <span className="text-green-400 flex items-center gap-2">● Connected <span className="text-xs text-gray-500">({ragQuery.data.ollama.models.length} models)</span></span>
                            ) : (
                                <span className="text-red-400">● Offline</span>
                            )}
                        </div>
                    </div>
                    <Brain className="w-8 h-8 text-gray-600 opacity-20" />
                </div>
                <div className="glass p-4 flex items-center justify-between">
                    <div>
                        <div className="text-sm text-gray-400">Qdrant Vector DB</div>
                        <div className="text-lg font-bold">
                            {ragQuery.data?.qdrant.connected ? (
                                <span className="text-green-400 flex items-center gap-2">● Connected <span className="text-xs text-gray-500">({ragQuery.data.qdrant.collections} collections)</span></span>
                            ) : (
                                <span className="text-red-400">● Offline</span>
                            )}
                        </div>
                    </div>
                    <DatabaseIcon className="w-8 h-8 text-gray-600 opacity-20" />
                </div>
            </div>

            {/* Agents Grid */}
            <h3 className="text-lg font-semibold flex items-center gap-2">
                <Bot className="w-5 h-5 text-purple-400" /> Agent Control Panel
            </h3>

            {agentsQuery.isLoading ? (
                <div className="text-center py-10 text-gray-500">Loading agents status...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {/* Render known agents first, then others */}
                    {Object.entries(agentsQuery.data?.agents || {}).map(([key, info]) => {
                        const ui = getAgentUI(key);
                        return (
                            <div key={key} className="glass p-6 relative overflow-hidden group">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-lg bg-gray-800`}>
                                            {ui.icon}
                                        </div>
                                        <div>
                                            <h4 className="font-bold">{ui.label}</h4>
                                            <p className="text-xs text-gray-500">{ui.desc}</p>
                                        </div>
                                    </div>
                                    {info.running ? (
                                        <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full animate-pulse">Running</span>
                                    ) : (
                                        <span className="text-xs bg-gray-700 text-gray-400 px-2 py-1 rounded-full">Stopped</span>
                                    )}
                                </div>
                                <div className="mt-4 flex justify-between items-center">
                                    <code className="text-[10px] text-gray-600 bg-black/20 px-2 py-1 rounded truncate max-w-[120px]" title={info.script}>
                                        {info.script.split('/').pop()}
                                    </code>
                                    <button
                                        onClick={() => startMutation.mutate(key)}
                                        disabled={info.running || startMutation.isPending}
                                        className={`btn-primary text-xs px-3 py-1 flex items-center gap-2 ${info.running ? 'opacity-50 cursor-not-allowed' : ''}`}
                                    >
                                        {startMutation.isPending && !logs ? <Loader className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                                        Start
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Quick Actions */}
            <div className="flex gap-4 flex-wrap pt-4 border-t border-gray-800">
                <button onClick={() => triggerMutation.mutate('checkmk')} className="btn-secondary text-sm flex items-center gap-2">
                    <RefreshCw className="w-4 h-4" /> Sync CheckMK
                </button>
                <button onClick={() => triggerMutation.mutate('forensic')} className="btn-secondary text-sm flex items-center gap-2">
                    <Brain className="w-4 h-4" /> Run AI Analysis
                </button>
                <button onClick={() => triggerMutation.mutate('watcher')} className="btn-secondary text-sm flex items-center gap-2">
                    <Eye className="w-4 h-4" /> Trigger Watcher
                </button>
            </div>

            {/* Process Log Modal */}
            {logVisible && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
                    <div className="glass w-full max-w-2xl flex flex-col max-h-[80vh]">
                        <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-gray-900/50">
                            <h3 className="font-mono flex items-center gap-2">
                                <TerminalIcon className="w-4 h-4 text-green-400" />
                                Agent Execution Log
                            </h3>
                            <button onClick={() => { setLogVisible(false); setLogs(null); }} className="hover:text-white text-gray-400">
                                <XCircle className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-1 bg-black/50">
                            {!logs ? (
                                <div className="flex items-center gap-2 text-yellow-400">
                                    <Loader className="w-4 h-4 animate-spin" /> Starting agent process...
                                </div>
                            ) : (
                                logs.output.map((line, i) => (
                                    <div key={i} className={`border-l-2 pl-2 ${line.includes('Error') || line.includes('❌') ? 'border-red-500 text-red-300' : 'border-gray-800 text-gray-300'}`}>
                                        {line}
                                    </div>
                                ))
                            )}
                            {logs && (
                                <div className={`mt-4 p-2 rounded ${logs.success ? 'bg-green-900/20 text-green-400' : 'bg-red-900/20 text-red-400'}`}>
                                    Process exited with code {logs.exit_code ?? 'unknown'}
                                </div>
                            )}
                        </div>
                        <div className="p-4 border-t border-gray-700 bg-gray-900/50 text-right">
                            <button onClick={() => { setLogVisible(false); setLogs(null); }} className="btn-secondary text-xs">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function DatabaseIcon({ className }: { className?: string }) {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>
    );
}
