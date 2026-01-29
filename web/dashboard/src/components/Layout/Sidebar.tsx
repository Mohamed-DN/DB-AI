import {
    LayoutDashboard,
    Database,
    Server,
    Bell,
    MessageSquare,
    Settings,
    Mail,
    Compass,
    Bot,
    BarChart3,
    Activity,
    ShieldCheck,
    ChevronLeft,
    ChevronRight,
    Monitor
} from 'lucide-react';

export type Tab = 'dashboard' | 'inventory' | 'hosts' | 'alerts' | 'chat' | 'mailbox' | 'explorer' | 'agents' | 'metrics' | 'settings' | 'monitoring' | 'admin' | 'oem';

interface SidebarProps {
    activeTab: Tab;
    setActiveTab: (tab: Tab) => void;
    isCollapsed: boolean;
    toggleCollapse: () => void;
}

export default function Sidebar({ activeTab, setActiveTab, isCollapsed, toggleCollapse }: SidebarProps) {

    const menuGroups = [
        {
            title: "Overview",
            items: [
                { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
                { id: 'monitoring', label: 'Monitoring', icon: Activity },
            ]
        },
        {
            title: "Infrastructure",
            items: [
                { id: 'inventory', label: 'Databases', icon: Database },
                { id: 'hosts', label: 'Hosts', icon: Server },
                { id: 'agents', label: 'Agents', icon: Bot },
            ]
        },
        {
            title: "Operations",
            items: [
                { id: 'alerts', label: 'Alerts', icon: Bell },
                { id: 'metrics', label: 'Metrics', icon: BarChart3 },
                { id: 'explorer', label: 'Data Explorer', icon: Compass },
            ]
        },
        {
            title: "Collaboration",
            items: [
                { id: 'chat', label: 'AI Assistant', icon: MessageSquare },
                { id: 'mailbox', label: 'Mailbox', icon: Mail },
            ]
        },
        {
            title: "System",
            items: [
                { id: 'admin', label: 'Admin Portal', icon: ShieldCheck },
                { id: 'oem', label: 'OEM Bridge', icon: Monitor },
                { id: 'settings', label: 'Settings', icon: Settings },
            ]
        }
    ] as const;

    return (
        <aside
            className={`glass border-r border-gray-800 transition-all duration-300 flex flex-col
        ${isCollapsed ? 'w-20' : 'w-64'} 
        fixed left-0 top-0 h-screen z-40 bg-gray-900/95 backdrop-blur-xl`}
        >
            {/* Brand */}
            <div className="h-16 flex items-center justify-center border-b border-gray-800">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                        <Database className="w-4 h-4 text-white" />
                    </div>
                    {!isCollapsed && (
                        <h1 className="font-bold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                            NEXI SENTINEL
                        </h1>
                    )}
                </div>
            </div>

            {/* Navigation */}
            <div className="flex-1 overflow-y-auto py-6 px-3 scrollbar-hide space-y-6">
                {menuGroups.map((group, idx) => (
                    <div key={idx} className="space-y-1">
                        {!isCollapsed && (
                            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 mb-2">
                                {group.title}
                            </h3>
                        )}
                        {group.items.map((item) => {
                            const isActive = activeTab === item.id;
                            return (
                                <button
                                    key={item.id}
                                    onClick={() => setActiveTab(item.id as Tab)}
                                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group
                    ${isActive
                                            ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]'
                                            : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
                                        }
                    ${isCollapsed ? 'justify-center' : ''}
                  `}
                                    title={isCollapsed ? item.label : ''}
                                >
                                    <item.icon
                                        className={`w-5 h-5 transition-transform duration-300 
                      ${isActive ? 'scale-110' : 'group-hover:scale-110'}
                      ${isCollapsed ? '' : ''}
                    `}
                                    />
                                    {!isCollapsed && (
                                        <span className="text-sm font-medium truncate">{item.label}</span>
                                    )}

                                    {/* Active Indicator Line (Left) */}
                                    {isActive && !isCollapsed && (
                                        <div className="absolute left-0 w-1 h-6 bg-blue-500 rounded-r-full" />
                                    )}
                                </button>
                            );
                        })}
                    </div>
                ))}
            </div>

            {/* Collapse Toggle */}
            <div className="p-4 border-t border-gray-800 flex justify-end">
                <button
                    onClick={toggleCollapse}
                    className="p-2 rounded-lg text-gray-500 hover:text-white hover:bg-gray-800 transition-colors"
                >
                    {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                </button>
            </div>
        </aside>
    );
}
