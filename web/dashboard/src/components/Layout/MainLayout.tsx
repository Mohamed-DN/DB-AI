import { useState, useEffect, type ReactNode } from 'react';
import Sidebar, { type Tab } from './Sidebar';
import Header from './Header';
import CommandPalette from '../Shared/CommandPalette';

interface MainLayoutProps {
    children: ReactNode;
    activeTab: Tab;
    setActiveTab: (tab: Tab) => void;
    user: any;
    logout: () => void;
    isPaused: boolean;
    togglePause: () => void;
}

const pageTitles: Record<Tab, string> = {
    dashboard: 'Dashboard Overview',
    inventory: 'Database Inventory',
    hosts: 'Host Inventory',
    alerts: 'System Alerts',
    chat: 'AI Assistant',
    mailbox: 'Communications',
    explorer: 'Data Explorer',
    agents: 'Agent Control Panel',
    metrics: 'Database Metrics',
    settings: 'Configuration',
    monitoring: 'Real-Time Monitoring',
    admin: 'Admin Portal & Tools',
    oem: 'Oracle Enterprise Manager',
};

export default function MainLayout({
    children,
    activeTab,
    setActiveTab,
    user,
    logout,
    isPaused,
    togglePause
}: MainLayoutProps) {
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
        const saved = localStorage.getItem('nexi-sidebar-collapsed');
        return saved === 'true';
    });
    const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);

    useEffect(() => {
        localStorage.setItem('nexi-sidebar-collapsed', String(isSidebarCollapsed));
    }, [isSidebarCollapsed]);

    // Global Keyboard Shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Cmd+K or Ctrl+K
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                setIsCommandPaletteOpen(prev => !prev);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    return (
        <div className="min-h-screen bg-[#0a0f1a] text-gray-100 font-sans selection:bg-blue-500/30">
            <CommandPalette
                isOpen={isCommandPaletteOpen}
                onClose={() => setIsCommandPaletteOpen(false)}
                onNavigate={(tab) => setActiveTab(tab as Tab)}
            />

            {/* Sidebar */}
            <Sidebar
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                isCollapsed={isSidebarCollapsed}
                toggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            />

            {/* Main Content Area */}
            <div
                className={`transition-all duration-300 min-h-screen flex flex-col
          ${isSidebarCollapsed ? 'pl-20' : 'pl-64'}
        `}
            >
                <Header
                    pageTitle={pageTitles[activeTab]}
                    user={user}
                    logout={logout}
                    isPaused={isPaused}
                    togglePause={togglePause}
                    onSearchClick={() => setIsCommandPaletteOpen(true)}
                />

                <main className="flex-1 p-6 overflow-x-hidden">
                    <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
}
