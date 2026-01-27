import { Bot, Play, Square, CheckCircle, XCircle, Loader, Terminal as TerminalIcon, Brain, RefreshCw, Eye, Clock, Settings, X, Activity, ExternalLink } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useState } from 'react';

const API_BASE = '/api';  // Vite proxy routes to backend

// --- Types ---
interface AgentInfo {
    script: string;
    running: boolean;
}

interface AgentsStatus {
    agents: Record<string, AgentInfo>;
}

interface RagStatus {
    ollama: { status: string; models?: string[]; url?: string };
    qdrant: { status: string; collections?: string[]; url?: string };
}

interface ProcessResult {
    status: string;
    agent: string;
    exit_code?: number;
    output: string[];
    success: boolean;
}

interface AgentConfig {
    scout_interval: number;
    collector_interval: number;
    watcher_interval: number;
    criticalalert_interval: number;
    forensicanalyzer_interval: number;
    checkmk_bridge_interval: number;
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

const getConfig = async (): Promise<AgentConfig> => {
    const { data } = await axios.get(`${API_BASE}/config`);
    return data;
};

const updateConfig = async (config: Partial<AgentConfig>): Promise<any> => {
    const { data } = await axios.post(`${API_BASE}/config`, config);
    return data;
};

const startAgent = async (name: string): Promise<ProcessResult> => {
    const { data } = await axios.post(`${API_BASE}/agents/start/${name}`);
    return data;
};

const stopAgent = async (name: string): Promise<any> => {
    const { data } = await axios.post(`${API_BASE}/agents/stop/${name}`);
    return data;
};

// --- Parsed Agent List for UI ---
const AGENT_UI: Record<string, { label: string; desc: string; icon: any; configKey: string }> = {
    scout: { label: 'Scout Agent', desc: 'Auto-discovery', icon: <Bot className="w-5 h-5 text-purple-400" />, configKey: 'scout_interval' },
    collector: { label: 'Metric Collector', desc: 'Database telemetry', icon: <RefreshCw className="w-5 h-5 text-blue-400" />, configKey: 'collector_interval' },
    watcher: { label: 'Log Watcher', desc: 'Live log monitoring', icon: <Eye className="w-5 h-5 text-yellow-400" />, configKey: 'watcher_interval' },
    criticalalert: { label: 'Critical Alerter', desc: 'Alert processing', icon: <TerminalIcon className="w-5 h-5 text-red-400" />, configKey: 'criticalalert_interval' },
    forensicanalyzer: { label: 'Forensic AI', desc: 'Root cause analysis', icon: <Brain className="w-5 h-5 text-pink-400" />, configKey: 'forensicanalyzer_interval' },
    checkmk_bridge: { label: 'CheckMK Bridge', desc: 'CheckMK sync', icon: <CheckCircle className="w-5 h-5 text-green-400" />, configKey: 'checkmk_bridge_interval' },
};

// --- Settings Modal Component ---
function SettingsModal({ isOpen, onClose, config, onSave }: {
    isOpen: boolean;
    onClose: () => void;
    config: AgentConfig | undefined;
    onSave: (newConfig: Partial<AgentConfig>) => void;
}) {
    const [localConfig, setLocalConfig] = useState<Partial<AgentConfig>>({});

    if (!isOpen || !config) return null;

    const handleSave = () => {
        onSave(localConfig);
        onClose();
    };

    const getValue = (key: keyof AgentConfig) => localConfig[key] ?? config[key] ?? 60;
    const setValue = (key: keyof AgentConfig, value: number) => {
        setLocalConfig(prev => ({ ...prev, [key]: value }));
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
            <div className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl border border-gray-700/50 shadow-2xl w-[500px] overflow-hidden">
                <div className="h-1 bg-gradient-to-r from-purple-500 via-blue-500 to-cyan-500" />

                <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            <Settings className="w-5 h-5 text-purple-400" />
                            Agent Intervals
                        </h2>
                        <button onClick={onClose} className="text-gray-400 hover:text-white">
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    <div className="space-y-4">
                        {Object.entries(AGENT_UI).map(([key, ui]) => (
                            <div key={key} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                                <div className="flex items-center gap-3">
                                    {ui.icon}
                                    <span className="font-medium">{ui.label}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Clock className="w-4 h-4 text-gray-500" />
                                    <input
                                        type="number"
                                        min="5"
                                        max="3600"
                                        value={getValue(ui.configKey as keyof AgentConfig)}
                                        onChange={(e) => setValue(ui.configKey as keyof AgentConfig, parseInt(e.target.value) || 60)}
                                        className="w-20 px-2 py-1 bg-gray-900 border border-gray-700 rounded text-center text-sm"
                                    />
                                    <span className="text-xs text-gray-500">sec</span>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="mt-6 flex justify-end gap-3">
                        <button onClick={onClose} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors">
                            Cancel
                        </button>
                        <button onClick={handleSave} className="px-4 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg transition-colors font-medium">
                            Save Changes
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

// --- Action Result Modal ---
function ActionModal({ isOpen, onClose, title, message, success }: {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    message: string;
    success: boolean;
}) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
            <div className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl border border-gray-700/50 shadow-2xl w-[400px] overflow-hidden">
                <div className={`h-1 ${success ? 'bg-green-500' : 'bg-red-500'}`} />

                <div className="p-8 text-center">
                    <div className="flex justify-center mb-4">
                        {success ? (
                            <CheckCircle className="w-16 h-16 text-green-500" />
                        ) : (
                            <XCircle className="w-16 h-16 text-red-500" />
                        )}
                    </div>
                    <h2 className="text-xl font-bold mb-2">{title}</h2>
                    <p className="text-gray-400 mb-6">{message}</p>
                    <button onClick={onClose} className={`w-full py-3 rounded-lg font-medium ${success ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function AgentsPanel() {
    const queryClient = useQueryClient();
    const [logVisible, setLogVisible] = useState(false);
    const [logs, setLogs] = useState<ProcessResult | null>(null);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const [actionResult, setActionResult] = useState<{ title: string; message: string; success: boolean } | null>(null);

    // Queries
    const agentsQuery = useQuery({ queryKey: ['agentsStatus'], queryFn: getAgentsStatus, refetchInterval: 5000 });
    const ragQuery = useQuery({ queryKey: ['ragStatus'], queryFn: getRagStatus, refetchInterval: 10000 });
    const configQuery = useQuery({ queryKey: ['agentConfig'], queryFn: getConfig });

    // Mutations
    const startMutation = useMutation({
        mutationFn: startAgent,
        onMutate: () => setLogVisible(true),
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

    const stopMutation = useMutation({
        mutationFn: stopAgent,
        onSuccess: (data) => {
            setActionResult({ title: 'Agent Stopped', message: data.status || 'Agent stopped successfully', success: true });
            queryClient.invalidateQueries({ queryKey: ['agentsStatus'] });
        },
        onError: (error: any) => {
            setActionResult({ title: 'Stop Failed', message: error.response?.data?.detail || error.message, success: false });
        }
    });

    const configMutation = useMutation({
        mutationFn: updateConfig,
        onSuccess: () => {
            setActionResult({ title: 'Settings Saved', message: 'Agent intervals updated successfully!', success: true });
            queryClient.invalidateQueries({ queryKey: ['agentConfig'] });
        },
        onError: (error: any) => {
            setActionResult({ title: 'Save Failed', message: error.response?.data?.detail || error.message, success: false });
        }
    });

    const getAgentUI = (key: string) => AGENT_UI[key] || { label: key, desc: 'Agent Script', icon: <Bot className="w-5 h-5" />, configKey: '' };

    return (
        <div className="space-y-6">
            {/* RAG Status Header */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="glass p-4 flex items-center justify-between">
                    <div>
                        <div className="text-sm text-gray-400">Ollama LLM</div>
                        <div className="text-lg font-bold flex items-center gap-2">
                            {ragQuery.data?.ollama.status === 'Connected' ? (
                                <span className="text-green-400 flex items-center gap-2">Connected <span className="text-xs text-gray-500">({ragQuery.data.ollama.models?.length || 0} mod)</span></span>
                            ) : (
                                <span className="text-red-400">{ragQuery.data?.ollama.status || 'Offline'}</span>
                            )}
                        </div>
                    </div>
                    <Brain className="w-8 h-8 text-gray-600 opacity-20" />
                </div>
                <div className="glass p-4 flex items-center justify-between">
                    <div>
                        <div className="text-sm text-gray-400">Qdrant Vector DB</div>
                        <div className="text-lg font-bold">
                            {ragQuery.data?.qdrant.status === 'Connected' ? (
                                <span className="text-green-400 flex items-center gap-2">Connected <span className="text-xs text-gray-500">({ragQuery.data.qdrant.collections?.length || 0} col)</span></span>
                            ) : (
                                <span className="text-red-400">{ragQuery.data?.qdrant.status || 'Offline'}</span>
                            )}
                        </div>
                    </div>
                    <DatabaseIcon className="w-8 h-8 text-gray-600 opacity-20" />
                </div>
                <div className="glass p-4 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors" onClick={() => window.open('http://localhost:3001', '_blank')}>
                    <div>
                        <div className="text-sm text-gray-400">Langfuse Tracing</div>
                        <div className="text-lg font-bold">
                            <span className="text-green-400">Active</span>
                        </div>
                        <div className="text-xs text-blue-400 mt-1 flex items-center gap-1">Open Dashboard <ExternalLink className="w-3 h-3" /></div>
                    </div>
                    <Activity className="w-8 h-8 text-purple-600 opacity-20" />
                </div>
                <div className="glass p-4 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors" onClick={() => window.open('http://localhost:8000/docs', '_blank')}>
                    <div>
                        <div className="text-sm text-gray-400">LangGraph Agents</div>
                        <div className="text-lg font-bold">
                            <span className="text-green-400">Active</span>
                        </div>
                        <div className="text-xs text-blue-400 mt-1 flex items-center gap-1">View API Docs <ExternalLink className="w-3 h-3" /></div>
                    </div>
                    <Bot className="w-8 h-8 text-pink-600 opacity-20" />
                </div>
            </div>

            {/* Agents List Header */}
            <div className="flex items-center justify-end">
                <button
                    onClick={() => setSettingsOpen(true)}
                    className="btn-secondary text-sm flex items-center gap-2"
                >
                    <Settings className="w-4 h-4" /> Configure Intervals
                </button>
            </div>

            {agentsQuery.isLoading ? (
                <div className="text-center py-10 text-gray-500">Loading agents status...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(agentsQuery.data?.agents || {}).map(([key, info]) => {
                        const ui = getAgentUI(key);
                        const interval = configQuery.data?.[ui.configKey as keyof AgentConfig];
                        return (
                            <div key={key} className="glass p-6 relative overflow-hidden group hover:border-purple-500/30 transition-all">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-lg ${info.running ? 'bg-green-900/30' : 'bg-gray-800'}`}>
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

                                {/* Interval Display */}
                                {interval !== undefined && (
                                    <div className="text-xs text-gray-500 mb-3 flex items-center gap-1">
                                        <Clock className="w-3 h-3" /> Every {interval}s
                                    </div>
                                )}

                                <div className="flex justify-between items-center gap-2">
                                    <code className="text-[10px] text-gray-600 bg-black/20 px-2 py-1 rounded truncate flex-1" title={info.script}>
                                        {info.script.split(/[\\/]/).pop()}
                                    </code>
                                    <div className="flex gap-2">
                                        {info.running ? (
                                            <button
                                                onClick={() => stopMutation.mutate(key)}
                                                disabled={stopMutation.isPending}
                                                className="p-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
                                                title="Stop Agent"
                                            >
                                                <Square className="w-4 h-4" />
                                            </button>
                                        ) : (
                                            <button
                                                onClick={() => startMutation.mutate(key)}
                                                disabled={startMutation.isPending}
                                                className="p-2 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-colors"
                                                title="Start Agent"
                                            >
                                                <Play className="w-4 h-4" />
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Settings Modal */}
            <SettingsModal
                isOpen={settingsOpen}
                onClose={() => setSettingsOpen(false)}
                config={configQuery.data}
                onSave={(newConfig) => configMutation.mutate(newConfig)}
            />

            {/* Action Result Modal */}
            {actionResult && (
                <ActionModal
                    isOpen={!!actionResult}
                    onClose={() => setActionResult(null)}
                    title={actionResult.title}
                    message={actionResult.message}
                    success={actionResult.success}
                />
            )}

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
                                logs.output.map((line, i) => {
                                    const normalizedLine = line.toLowerCase();
                                    const isError = normalizedLine.includes('error') || normalizedLine.includes('failed');
                                    return (
                                        <div key={i} className={`border-l-2 pl-2 ${isError ? 'border-red-500 text-red-300' : 'border-gray-800 text-gray-300'}`}>
                                            {line}
                                        </div>
                                    );
                                })
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
