import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ConnectionProvider } from './context/ConnectionContext';
import { useSystemStatus } from './hooks/useDatabases';
import './index.css';

// Components
import MainLayout from './components/Layout/MainLayout';
import type { Tab } from './components/Layout/Sidebar';
import Login from './components/Auth/Login';
import SystemProgressModal, { type ProgressEvent } from './components/System/SystemProgressModal';

// Views
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
import AdminPortal from './components/Admin/AdminPortal';
import OEMDashboard from './components/Admin/OEM/OEMDashboard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function TelemetryPanel() {
  return (
    <div className="glass p-8 flex items-center justify-center gap-6 border border-blue-500/20 bg-blue-500/5">
      {/* Dynamic Equalizer Animation */}
      <div className="flex gap-2 items-end h-12">
        <div className="w-2.5 h-12 bg-blue-500 rounded-full telemetry-bar"></div>
        <div className="w-2.5 h-12 bg-indigo-500 rounded-full telemetry-bar" style={{ animationDelay: '0.1s' }}></div>
        <div className="w-2.5 h-12 bg-cyan-500 rounded-full telemetry-bar" style={{ animationDelay: '0.2s' }}></div>
        <div className="w-2.5 h-12 bg-emerald-500 rounded-full telemetry-bar" style={{ animationDelay: '0.3s' }}></div>
        <div className="w-2.5 h-12 bg-purple-500 rounded-full telemetry-bar" style={{ animationDelay: '0.4s' }}></div>
      </div>
      <div className="flex flex-col">
        <span className="text-gray-200 font-semibold tracking-wide">SYSTEM TELEMETRY</span>
        <div className="flex items-center gap-2 mt-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-xs text-blue-400 font-mono">LIVE DATA STREAM ACTIVE</span>
        </div>
      </div>
    </div>
  );
}

function AppContent() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const { data: systemStatus } = useSystemStatus();
  const { user, logout, isAuthenticated, isLoading } = useAuth();
  const [isPaused, setIsPaused] = useState(false);

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

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a0f1a] flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 border-t-2 border-b-2 border-blue-500 rounded-full animate-spin mb-4"></div>
          <p className="text-gray-400 tracking-wider text-sm font-mono">INITIALIZING SYSTEM...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return <Login />;

  const handleTogglePause = async () => {
    const targetState = !isPaused;
    const statusStr = targetState ? 'PAUSED' : 'RUNNING';

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
    queryClient.invalidateQueries({ queryKey: ['systemStatus'] });
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div className="space-y-6">
            <DashboardStats />
            <TelemetryPanel />
          </div>
        );
      case 'inventory': return <InventoryTable />;
      case 'hosts': return <HostsTable />;
      case 'alerts': return <AlertsPanel />;
      case 'chat': return <AIChat />;
      case 'mailbox': return <MailboxPanel />;
      case 'explorer': return <ExplorerPanel />;
      case 'agents': return <AgentsPanel />;
      case 'metrics': return <MetricsContainer />;
      case 'monitoring': return <MonitoringDashboard />;
      case 'admin': return <AdminPortal onNavigate={(tab) => setActiveTab(tab as Tab)} />;
      case 'oem': return <OEMDashboard />;
      case 'settings': return <SettingsPanel onNavigateToAgents={() => setActiveTab('agents')} />;
      default: return null;
    }
  };

  return (
    <MainLayout
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      user={user}
      logout={logout}
      isPaused={isPaused}
      togglePause={handleTogglePause}
    >
      <SystemProgressModal
        isOpen={showProgressModal}
        onClose={() => setShowProgressModal(false)}
        events={progressEvents}
        isComplete={isOperationComplete}
        title={operationTitle}
      />
      {renderContent()}
    </MainLayout>
  );
}

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
