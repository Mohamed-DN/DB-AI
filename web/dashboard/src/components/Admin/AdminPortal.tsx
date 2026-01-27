import React from 'react';
import { ExternalLink, Database, Activity, FileText, Server, BarChart3, ShieldCheck, ArrowRight } from 'lucide-react';

// Configuration for external tools
const TOOLS = [
    {
        id: 'mongo-express',
        title: 'MongoDB UI',
        description: 'Web-based administrative interface for MongoDB.',
        icon: Database,
        color: 'text-green-400',
        bgColor: 'bg-green-500/10',
        url: 'http://localhost:9081',
        category: 'Database'
    },
    {
        id: 'grafana',
        title: 'Grafana',
        description: 'Operational dashboards and metrics visualization.',
        icon: BarChart3,
        color: 'text-orange-400',
        bgColor: 'bg-orange-500/10',
        url: 'http://localhost:3003',
        category: 'Monitoring'
    },
    {
        id: 'langfuse',
        title: 'Langfuse',
        description: 'LLM observability, tracing, and prompt management.',
        icon: Activity,
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/10',
        url: 'http://localhost:3001',
        category: 'AI & LLM'
    },
    {
        id: 'victoriametrics',
        title: 'VictoriaMetrics',
        description: 'High-performance time series database UI.',
        icon: Server,
        color: 'text-red-400',
        bgColor: 'bg-red-500/10',
        url: 'http://localhost:8428/vmui',
        category: 'Database'
    },
    {
        id: 'oem',
        title: 'OEM Database',
        description: 'Oracle Enterprise Manager instances and metrics.',
        icon: ShieldCheck,
        color: 'text-purple-400',
        bgColor: 'bg-purple-500/10',
        url: '/admin/oem', // To be implemented
        category: 'Enterprise'
    }
];

interface AdminPortalProps {
    onNavigate: (tab: string) => void;
}

const AdminPortal: React.FC<AdminPortalProps> = ({ onNavigate }) => {
    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <div className="flex flex-col gap-2 mb-6">
                <h1 className="text-3xl font-bold tracking-tight text-white">Admin Portal</h1>
                <p className="text-gray-400">
                    Central hub for system administration and external tools access.
                </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {TOOLS.map((tool) => (
                    <div key={tool.id} className="glass p-6 rounded-xl hover:border-blue-500/30 transition-all hover:scale-[1.02] group">
                        <div className="flex items-start justify-between mb-4">
                            <div className={`p-3 rounded-xl ${tool.bgColor}`}>
                                <tool.icon className={`h-6 w-6 ${tool.color}`} />
                            </div>
                            <span className="text-xs font-medium px-2 py-1 rounded-full bg-gray-800 text-gray-400 border border-gray-700">
                                {tool.category}
                            </span>
                        </div>

                        <h3 className="text-xl font-bold mb-2 text-white">{tool.title}</h3>
                        <p className="text-sm text-gray-400 mb-6 h-10">
                            {tool.description}
                        </p>

                        {tool.url.startsWith('http') ? (
                            <button
                                className="w-full py-2 px-4 rounded-lg bg-gray-800 hover:bg-gray-700 border border-gray-700 text-sm font-medium flex items-center justify-center gap-2 transition-colors group-hover:border-blue-500/50"
                                onClick={() => window.open(tool.url, '_blank')}
                            >
                                Open Tool <ExternalLink className="h-4 w-4" />
                            </button>
                        ) : (
                            <button
                                className="w-full py-2 px-4 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 text-blue-300 text-sm font-medium flex items-center justify-center gap-2 transition-colors"
                                onClick={() => {
                                    // Extract tab name from internal URL (e.g. /admin/oem -> oem)
                                    const tab = tool.url.split('/').pop();
                                    if (tab) onNavigate(tab);
                                }}
                            >
                                Manage <ArrowRight className="h-4 w-4" />
                            </button>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default AdminPortal;
