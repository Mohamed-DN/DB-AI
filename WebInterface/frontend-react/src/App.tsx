import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
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
  RefreshCw,
  Pause,
  Play,
  ExternalLink,
  BarChart3
} from 'lucide-react';
import DashboardStats from './components/Dashboard/DashboardStats';
import InventoryTable from './components/Inventory/InventoryTable';
import HostsTable from './components/Hosts/HostsTable';
import AlertsPanel from './components/Alerts/AlertsPanel';
import AIChat from './components/AIChat/AIChat';
import MailboxPanel from './components/Mailbox/MailboxPanel';
import ExplorerPanel from './components/Explorer/ExplorerPanel';
import AgentsPanel from './components/Agents/AgentsPanel';
import SettingsPanel from './components/Settings/SettingsPanel';
import { MetricsPanel } from './components/Metrics';
import { useAutoDiscovery, useSystemStatus, useSetSystemStatus } from './hooks/useDatabases';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

type Tab = 'dashboard' | 'inventory' | 'hosts' | 'alerts' | 'chat' | 'mailbox' | 'explorer' | 'agents' | 'metrics' | 'settings';

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
};

function Navigation({
  activeTab,
  setActiveTab
}: {
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
}) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'inventory', label: 'Inventory', icon: Database },
    { id: 'hosts', label: 'Hosts', icon: Server },
    { id: 'alerts', label: 'Alerts', icon: Bell },
    { id: 'chat', label: 'AI Chat', icon: MessageSquare },
    { id: 'mailbox', label: 'Mailbox', icon: Mail },
    { id: 'explorer', label: 'Explorer', icon: Compass },
    { id: 'agents', label: 'Agents', icon: Bot },
    { id: 'metrics', label: 'Metrics', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ] as const;

  return (
    <nav className="flex gap-2 flex-wrap">
      {navItems.map((item) => (
        <button
          key={item.id}
          onClick={() => setActiveTab(item.id as Tab)}
          className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
        >
          <item.icon className="w-4 h-4" />
          <span className="hidden md:inline">{item.label}</span>
        </button>
      ))}
    </nav>
  );
}

function TelemetryPanel() {
  return (
    <div className="glass p-8 mt-6 flex items-center justify-center gap-4">
      {/* Dynamic Equalizer Animation */}
      <div className="flex gap-2 items-end h-10">
        <div className="w-2 h-10 bg-blue-500 rounded-full telemetry-bar"></div>
        <div className="w-2 h-10 bg-purple-500 rounded-full telemetry-bar"></div>
        <div className="w-2 h-10 bg-cyan-500 rounded-full telemetry-bar"></div>
        <div className="w-2 h-10 bg-emerald-500 rounded-full telemetry-bar"></div>
        <div className="w-2 h-10 bg-indigo-500 rounded-full telemetry-bar"></div>
      </div>
      <div className="flex flex-col">
        <span className="text-gray-300 font-medium text-sm">Real-time telemetry</span>
        <span className="text-xs text-blue-400 animate-pulse">Streaming data...</span>
      </div>
    </div>
  );
}

function AppContent() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const autoDiscovery = useAutoDiscovery();
  const { data: systemStatus } = useSystemStatus();
  const setSystemStatus = useSetSystemStatus();
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (systemStatus) {
      setIsPaused(systemStatus.paused ?? systemStatus.status === 'PAUSED');
    }
  }, [systemStatus]);

  const handleTogglePause = () => {
    const newState = !isPaused;
    setIsPaused(newState);
    setSystemStatus.mutate(newState);
  };

  const openMongoDB = () => {
    // V2 uses 9081, V1 uses 8081. Default to V2 if not specified.
    const port = import.meta.env.VITE_MONGO_EXPRESS_PORT || '9081';
    window.open(`http://localhost:${port}`, '_blank');
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <>
            <DashboardStats />
            <TelemetryPanel />
          </>
        );
      case 'inventory':
        return <InventoryTable />;
      case 'hosts':
        return <HostsTable />;
      case 'alerts':
        return <AlertsPanel />;
      case 'chat':
        return <AIChat />;
      case 'mailbox':
        return <MailboxPanel />;
      case 'explorer':
        return <ExplorerPanel />;
      case 'agents':
        return <AgentsPanel />;
      case 'metrics':
        return <MetricsPanel />;
      case 'settings':
        return <SettingsPanel onNavigateToAgents={() => setActiveTab('agents')} />;
      default:
        return null;
    }
  };


  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="glass sticky top-0 z-50 px-4 py-3 mb-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Database className="w-4 h-4 text-white" />
            </div>
            <h1 className="text-lg font-bold tracking-wider">NEXI SENTINEL</h1>
          </div>

          {/* Navigation */}
          <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />

          {/* Right Actions */}
          <div className="flex items-center gap-2">
            {/* MongoDB Button */}
            <button
              onClick={openMongoDB}
              className="btn-secondary text-sm"
              title="Open MongoDB Express"
            >
              <ExternalLink className="w-4 h-4" />
              <span className="hidden md:inline">MongoDB</span>
            </button>

            {/* Pause/Play Button */}
            <button
              onClick={handleTogglePause}
              className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${isPaused
                ? 'bg-emerald-500 hover:bg-emerald-600 text-white'
                : 'bg-amber-500 hover:bg-amber-600 text-white'
                }`}
              title={isPaused ? 'Resume System' : 'Pause System'}
            >
              {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
              <span className="hidden md:inline">{isPaused ? 'Resume' : 'Pause'} System</span>
            </button>

            {/* Status Indicator */}
            <div className="flex items-center gap-2 px-3">
              <span className={`w-2 h-2 rounded-full ${isPaused ? 'bg-amber-400' : 'bg-emerald-500 animate-pulse'}`}></span>
              <span className="text-gray-400 text-sm hidden md:inline">
                {isPaused ? 'SYSTEM PAUSED' : 'SYSTEM ONLINE'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Page Title + Actions */}
      <div className="flex items-center justify-between px-4 mb-4">
        <h2 className="text-xl font-semibold">{pageTitles[activeTab]}</h2>
        <div className="flex gap-2">
          <button
            onClick={() => autoDiscovery.mutate()}
            className="btn-primary"
            disabled={autoDiscovery.isPending}
          >
            <RefreshCw className={`w-4 h-4 ${autoDiscovery.isPending ? 'animate-spin' : ''}`} />
            Auto-Discovery
          </button>
        </div>
      </div>

      {/* Main Content */}
      <main className="px-4 pb-6">
        {renderContent()}
      </main>
    </div>
  );
}

import { ConnectionProvider } from './context/ConnectionContext';

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConnectionProvider>
        <AppContent />
      </ConnectionProvider>
    </QueryClientProvider>
  );
}
