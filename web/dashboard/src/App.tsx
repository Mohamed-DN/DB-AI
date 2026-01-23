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
  BarChart3,
  Activity,
  LogOut,
  User
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
import { MetricsContainer } from './components/Metrics';
import { MonitoringDashboard } from './components/Monitoring';
import Login from './components/Auth/Login';
import { AuthProvider, useAuth } from './context/AuthContext';
import { useAutoDiscovery, useSystemStatus } from './hooks/useDatabases';
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

type Tab = 'dashboard' | 'inventory' | 'hosts' | 'alerts' | 'chat' | 'mailbox' | 'explorer' | 'agents' | 'metrics' | 'settings' | 'monitoring';

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
  monitoring: 'Real-Time Monitoring (Grafana/CheckMK)', // New Title
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
    { id: 'monitoring', label: 'Monitor', icon: Activity }, // Add Monitoring Item
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

import SystemProgressModal, { type ProgressEvent } from './components/System/SystemProgressModal';

function AppContent() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const autoDiscovery = useAutoDiscovery();
  const { data: systemStatus } = useSystemStatus();
  const { user, logout, hasPermission, isAuthenticated, isLoading } = useAuth();
  const [isPaused, setIsPaused] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Progress Modal State
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [progressEvents, setProgressEvents] = useState<ProgressEvent[]>([]);
  const [isOperationComplete, setIsOperationComplete] = useState(false);
  const [operationTitle, setOperationTitle] = useState('');

  useEffect(() => {
    if (systemStatus) {
      setIsPaused(systemStatus.paused ?? systemStatus.status === 'PAUSED');
    }
  }, [systemStatus]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <Login />;
  }

  const handleTogglePause = async () => {
    const targetState = !isPaused; // If paused=true, we want to Resume (running). If paused=false, we want to Pause.
    const statusStr = targetState ? 'PAUSED' : 'RUNNING';

    // Setup Modal
    setOperationTitle(targetState ? 'Pausing System Containers...' : 'Resuming System Containers...');
    setProgressEvents([]);
    setIsOperationComplete(false);
    setShowProgressModal(true);

    try {
      const response = await fetch('/api/system/status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: statusStr }),
      });

      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const event = JSON.parse(line) as ProgressEvent;
            setProgressEvents(prev => [...prev, event]);

            if (event.type === 'complete') {
              setIsOperationComplete(true);
              // Update local state to match final result
              setIsPaused(event.status === 'PAUSED');
            }
          } catch (e) {
            console.error("Error parsing stream event:", e);
          }
        }
      }
    } catch (error) {
      console.error("Stream error:", error);
      setProgressEvents(prev => [...prev, {
        type: 'progress',
        status: 'failed',
        container: 'System',
        message: String(error)
      }]);
      setIsOperationComplete(true);
    }

    // Invalidate query to refresh global status
    queryClient.invalidateQueries({ queryKey: ['systemStatus'] });
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
        return <MetricsContainer />;
      case 'monitoring': // Render new component
        return <MonitoringDashboard />;
      case 'settings':
        return <SettingsPanel onNavigateToAgents={() => setActiveTab('agents')} />;
      default:
        return null;
    }
  };


  return (
    <div className="min-h-screen">
      <SystemProgressModal
        isOpen={showProgressModal}
        onClose={() => setShowProgressModal(false)}
        events={progressEvents}
        isComplete={isOperationComplete}
        title={operationTitle}
      />

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

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-800/50 hover:bg-gray-700/50 transition-colors"
              >
                <User className="w-4 h-4" />
                <span className="hidden md:inline text-sm">{user?.username}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${user?.role === 'admin' ? 'bg-purple-500/20 text-purple-300' :
                    user?.role === 'operator' ? 'bg-blue-500/20 text-blue-300' :
                      'bg-gray-500/20 text-gray-300'
                  }`}>
                  {user?.role}
                </span>
              </button>

              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 glass rounded-lg shadow-lg py-1 z-50">
                  <div className="px-4 py-2 border-b border-gray-700">
                    <p className="text-sm font-medium">{user?.full_name || user?.username}</p>
                    <p className="text-xs text-gray-400">{user?.email}</p>
                  </div>
                  <button
                    onClick={() => { logout(); setShowUserMenu(false); }}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign Out
                  </button>
                </div>
              )}
            </div>

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
      <AuthProvider>
        <ConnectionProvider>
          <AppContent />
        </ConnectionProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
