import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  LayoutDashboard,
  Database,
  Server,
  Bell,
  MessageSquare,
  Settings,
  RefreshCw,
  Pause,
  Play
} from 'lucide-react';
import DashboardStats from './components/Dashboard/DashboardStats';
import InventoryTable from './components/Inventory/InventoryTable';
import AIChat from './components/AIChat/AIChat';
import { useAutoDiscovery } from './hooks/useDatabases';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      refetchOnWindowFocus: false,
    },
  },
});

type Tab = 'dashboard' | 'inventory' | 'hosts' | 'alerts' | 'ai-chat' | 'settings';

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
    { id: 'ai-chat', label: 'AI Chat', icon: MessageSquare },
    { id: 'settings', label: 'Settings', icon: Settings },
  ] as const;

  return (
    <nav className="flex gap-2 flex-wrap">
      {navItems.map((item) => (
        <button
          key={item.id}
          onClick={() => setActiveTab(item.id)}
          className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
        >
          <item.icon className="w-4 h-4" />
          <span>{item.label}</span>
        </button>
      ))}
    </nav>
  );
}

function AppContent() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [isPaused, setIsPaused] = useState(false);
  const autoDiscovery = useAutoDiscovery();

  const handleAutoDiscovery = () => {
    autoDiscovery.mutate();
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div className="space-y-6">
            <DashboardStats />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <h2 className="text-xl font-semibold mb-4">Database Inventory</h2>
                <InventoryTable />
              </div>
              <div>
                <h2 className="text-xl font-semibold mb-4">AI Assistant</h2>
                <AIChat />
              </div>
            </div>
          </div>
        );
      case 'inventory':
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Database Inventory</h2>
              <button
                onClick={handleAutoDiscovery}
                className="btn-primary"
                disabled={autoDiscovery.isPending}
              >
                <RefreshCw className={`w-4 h-4 ${autoDiscovery.isPending ? 'animate-spin' : ''}`} />
                Auto-Discovery
              </button>
            </div>
            <InventoryTable />
          </div>
        );
      case 'ai-chat':
        return (
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold mb-6">AI Database Assistant</h2>
            <AIChat />
          </div>
        );
      case 'hosts':
        return (
          <div className="glass p-8 text-center text-gray-400">
            <Server className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>Host Management - Coming Soon</p>
          </div>
        );
      case 'alerts':
        return (
          <div className="glass p-8 text-center text-gray-400">
            <Bell className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>Alert Center - Coming Soon</p>
          </div>
        );
      case 'settings':
        return (
          <div className="glass p-8 text-center text-gray-400">
            <Settings className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>Settings - Coming Soon</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="glass sticky top-0 z-50 px-6 py-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[--nexi-primary] to-purple-600 flex items-center justify-center">
                <Database className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight">NEXI SENTINEL</h1>
                <p className="text-xs text-gray-400">AI Database Management</p>
              </div>
            </div>
          </div>

          <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-gray-400">System Online</span>
            </div>
            <button
              onClick={() => setIsPaused(!isPaused)}
              className={`p-2 rounded-lg transition-colors ${isPaused
                  ? 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30'
                  : 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30'
                }`}
              title={isPaused ? 'Resume System' : 'Pause System'}
            >
              {isPaused ? <Play className="w-5 h-5" /> : <Pause className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="px-6 pb-6">
        {renderContent()}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
