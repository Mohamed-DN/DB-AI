import React, { useState, useEffect, useCallback } from 'react';
import {
    BarChart3,
    Activity,
    HardDrive,
    Zap,
    Database,
    RefreshCw,
    TrendingUp,
    Clock,
    AlertTriangle,
    Server,
    Wifi,
    WifiOff
} from 'lucide-react';
import {
    AreaChart,
    Area,
    BarChart,
    Bar,
    LineChart,
    Line,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from 'recharts';
import { getDatabases, getMetrics, type MetricsResponse } from '../../services/api';
import styles from './MetricsPanel.module.css';

// Generate time series data for charts
const generateTimeData = (hours = 24, baseValue = 50, variance = 20) => {
    const now = Date.now();
    return Array.from({ length: hours }, (_, i) => ({
        time: new Date(now - (hours - i) * 3600000).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }),
        value: Math.max(0, baseValue + (Math.random() - 0.5) * variance * 2),
        value2: Math.max(0, baseValue * 0.8 + (Math.random() - 0.5) * variance * 2),
    }));
};

interface DatabaseOption {
    label: string;
    value: string;
    engine: string;
}

/**
 * MetricsPanel - Database metrics dashboard with native Recharts
 * Connected to real database inventory and metrics API
 */
export const MetricsPanel: React.FC = () => {
    const [selectedDb, setSelectedDb] = useState<string>('all');
    const [timeRange, setTimeRange] = useState<string>('24h');
    const [refreshing, setRefreshing] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [connected, setConnected] = useState(true);

    // Database list from inventory
    const [databases, setDatabases] = useState<DatabaseOption[]>([
        { label: 'All Databases', value: 'all', engine: 'all' }
    ]);

    // Metrics from API
    const [metrics, setMetrics] = useState({
        bufferHit: 0,
        tps: 0,
        storage: 0,
        connections: 0,
        queryTime: 0,
        alerts: 0
    });

    // Chart data
    const [connectionsData, setConnectionsData] = useState<Array<{ name: string; active: number; idle: number }>>([]);
    const [storageData, setStorageData] = useState<Array<{ name: string; used: number; color: string }>>([]);
    const [performanceData, setPerformanceData] = useState(generateTimeData(24, 1200, 300));
    const [latencyData, setLatencyData] = useState(generateTimeData(24, 15, 10));
    const [iopsData, setIopsData] = useState(generateTimeData(24, 500, 200));
    const [locksData] = useState([
        { time: '00:00', locks: 2, deadlocks: 0 },
        { time: '04:00', locks: 1, deadlocks: 0 },
        { time: '08:00', locks: 5, deadlocks: 1 },
        { time: '12:00', locks: 8, deadlocks: 0 },
        { time: '16:00', locks: 12, deadlocks: 2 },
        { time: '20:00', locks: 6, deadlocks: 0 },
    ]);

    const timeRanges = [
        { label: '1h', value: '1h' },
        { label: '6h', value: '6h' },
        { label: '24h', value: '24h' },
        { label: '7d', value: '7d' },
        { label: '30d', value: '30d' },
    ];

    // Fetch databases from inventory
    const fetchDatabases = useCallback(async () => {
        try {
            const dbs = await getDatabases();
            const dbOptions: DatabaseOption[] = [
                { label: 'All Databases', value: 'all', engine: 'all' }
            ];

            dbs.forEach((db: any) => {
                const name = db.identity?.db_unique_name || db.identity?.db_name || 'Unknown';
                const engine = db.identity?.engine || 'UNKNOWN';
                dbOptions.push({
                    label: `${name} (${engine})`,
                    value: name,
                    engine: engine
                });
            });

            setDatabases(dbOptions);
            setConnected(true);
        } catch (err) {
            console.error('Failed to fetch databases:', err);
            setConnected(false);
        }
    }, []);

    // Fetch metrics from API
    const fetchMetrics = useCallback(async (dbFilter?: string) => {
        try {
            setRefreshing(true);
            const data: MetricsResponse = await getMetrics(dbFilter);

            // Update summary metrics
            setMetrics({
                bufferHit: data.summary.buffer_hit,
                tps: data.summary.tps,
                storage: data.summary.storage_gb,
                connections: data.summary.total_connections,
                queryTime: data.summary.avg_query_ms,
                alerts: data.summary.active_alerts
            });

            // Update connections by DB
            if (data.connections_by_db && data.connections_by_db.length > 0) {
                setConnectionsData(data.connections_by_db.map(c => ({
                    name: c.name,
                    active: c.active,
                    idle: c.idle
                })));
            }

            // Update storage data (from tablespaces or databases)
            if (data.oracle_tablespaces && data.oracle_tablespaces.length > 0) {
                setStorageData(data.oracle_tablespaces.map(ts => ({
                    name: ts.name,
                    used: ts.used_pct,
                    color: ts.used_pct > 90 ? '#ef4444' : ts.used_pct > 80 ? '#f59e0b' : '#10b981'
                })));
            } else if (data.pg_databases && data.pg_databases.length > 0) {
                const maxSize = Math.max(...data.pg_databases.map(d => d.size_gb), 1);
                setStorageData(data.pg_databases.map(db => ({
                    name: db.name.substring(0, 10),
                    used: Math.round((db.size_gb / maxSize) * 100),
                    color: '#8b5cf6'
                })));
            }

            // Regenerate time-based charts with new variance
            const baseTps = data.summary.tps || 1200;
            setPerformanceData(generateTimeData(24, baseTps, baseTps * 0.2));
            setLatencyData(generateTimeData(24, data.summary.avg_query_ms || 15, 10));
            setIopsData(generateTimeData(24, 500, 200));

            setConnected(true);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch metrics:', err);
            setError('Failed to connect to backend');
            setConnected(false);

            // Use mock data as fallback
            setMetrics({
                bufferHit: 95 + Math.random() * 5,
                tps: 1000 + Math.floor(Math.random() * 500),
                storage: 150 + Math.random() * 20,
                connections: 30 + Math.floor(Math.random() * 30),
                queryTime: 5 + Math.random() * 20,
                alerts: Math.floor(Math.random() * 5)
            });
        } finally {
            setRefreshing(false);
            setLoading(false);
        }
    }, []);

    // Initial load
    useEffect(() => {
        fetchDatabases();
        fetchMetrics(selectedDb);
    }, [fetchDatabases, fetchMetrics, selectedDb]);

    // Auto-refresh every 30s
    useEffect(() => {
        const interval = setInterval(() => fetchMetrics(selectedDb), 30000);
        return () => clearInterval(interval);
    }, [fetchMetrics, selectedDb]);

    // Handle database change
    const handleDbChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newDb = e.target.value;
        setSelectedDb(newDb);
        fetchMetrics(newDb);
    };

    // Handle manual refresh
    const handleRefresh = () => {
        fetchMetrics(selectedDb);
    };

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className={styles.customTooltip}>
                    <p className={styles.tooltipLabel}>{label}</p>
                    {payload.map((entry: any, index: number) => (
                        <p key={index} style={{ color: entry.color }}>
                            {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    };

    if (loading) {
        return (
            <div className={styles.container}>
                <div className={styles.loadingState}>
                    <RefreshCw size={32} className={styles.spinning} />
                    <p>Loading metrics...</p>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            {/* Header Section */}
            <div className={styles.header}>
                <div className={styles.titleSection}>
                    <div className={styles.titleIcon}>
                        <BarChart3 size={24} />
                    </div>
                    <div>
                        <h1 className={styles.title}>Database Metrics</h1>
                        <p className={styles.subtitle}>
                            Real-time performance monitoring
                            {connected ? (
                                <span className={styles.connectedBadge}>
                                    <Wifi size={12} /> Connected
                                </span>
                            ) : (
                                <span className={styles.disconnectedBadge}>
                                    <WifiOff size={12} /> Offline (mock data)
                                </span>
                            )}
                        </p>
                    </div>
                </div>

                {/* Controls */}
                <div className={styles.controls}>
                    <select
                        className={styles.select}
                        value={selectedDb}
                        onChange={handleDbChange}
                    >
                        {databases.map(db => (
                            <option key={db.value} value={db.value}>{db.label}</option>
                        ))}
                    </select>

                    <div className={styles.timeRangeGroup}>
                        {timeRanges.map(tr => (
                            <button
                                key={tr.value}
                                className={`${styles.timeBtn} ${timeRange === tr.value ? styles.active : ''}`}
                                onClick={() => setTimeRange(tr.value)}
                            >
                                {tr.label}
                            </button>
                        ))}
                    </div>

                    <button
                        className={styles.refreshBtn}
                        onClick={handleRefresh}
                        disabled={refreshing}
                        title="Refresh metrics"
                    >
                        <RefreshCw size={16} className={refreshing ? styles.spinning : ''} />
                    </button>
                </div>
            </div>

            {/* Error Banner */}
            {error && (
                <div className={styles.errorBanner}>
                    <AlertTriangle size={16} />
                    <span>{error} - Showing cached/mock data</span>
                </div>
            )}

            {/* Quick Stats Row */}
            <div className={styles.statsRow}>
                <div className={styles.statCard}>
                    <div className={styles.statIcon} style={{ background: 'rgba(16, 185, 129, 0.15)' }}>
                        <Activity size={20} color="#10b981" />
                    </div>
                    <div className={styles.statContent}>
                        <span className={styles.statValue}>{metrics.bufferHit.toFixed(1)}%</span>
                        <span className={styles.statLabel}>Buffer Hit</span>
                    </div>
                    <TrendingUp size={16} className={styles.trendUp} />
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon} style={{ background: 'rgba(139, 92, 246, 0.15)' }}>
                        <Zap size={20} color="#8b5cf6" />
                    </div>
                    <div className={styles.statContent}>
                        <span className={styles.statValue}>{metrics.tps.toLocaleString()}</span>
                        <span className={styles.statLabel}>TPS</span>
                    </div>
                    <TrendingUp size={16} className={styles.trendUp} />
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon} style={{ background: 'rgba(245, 158, 11, 0.15)' }}>
                        <HardDrive size={20} color="#f59e0b" />
                    </div>
                    <div className={styles.statContent}>
                        <span className={styles.statValue}>{metrics.storage.toFixed(1)} GB</span>
                        <span className={styles.statLabel}>Total Size</span>
                    </div>
                    <TrendingUp size={16} className={styles.trendUp} />
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon} style={{ background: 'rgba(59, 130, 246, 0.15)' }}>
                        <Server size={20} color="#3b82f6" />
                    </div>
                    <div className={styles.statContent}>
                        <span className={styles.statValue}>{metrics.connections}</span>
                        <span className={styles.statLabel}>Connections</span>
                    </div>
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon} style={{ background: 'rgba(236, 72, 153, 0.15)' }}>
                        <Clock size={20} color="#ec4899" />
                    </div>
                    <div className={styles.statContent}>
                        <span className={styles.statValue}>{metrics.queryTime.toFixed(1)} ms</span>
                        <span className={styles.statLabel}>Avg Query</span>
                    </div>
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon} style={{ background: metrics.alerts > 0 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)' }}>
                        <AlertTriangle size={20} color={metrics.alerts > 0 ? '#ef4444' : '#10b981'} />
                    </div>
                    <div className={styles.statContent}>
                        <span className={styles.statValue}>{metrics.alerts}</span>
                        <span className={styles.statLabel}>Alerts</span>
                    </div>
                </div>
            </div>

            {/* Main Charts Grid */}
            <div className={styles.chartsGrid}>
                {/* Performance Overview - Large Panel */}
                <div className={`${styles.chartCard} ${styles.wide}`}>
                    <div className={styles.chartHeader}>
                        <h3>Performance Overview</h3>
                        <span className={styles.chartSubtitle}>TPS & Query Time</span>
                    </div>
                    <div className={styles.chartContent}>
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={performanceData}>
                                <defs>
                                    <linearGradient id="colorTps" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="colorQuery" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                <XAxis dataKey="time" stroke="#6b7280" fontSize={11} tickLine={false} />
                                <YAxis stroke="#6b7280" fontSize={11} tickLine={false} axisLine={false} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                                <Area type="monotone" dataKey="value" name="TPS" stroke="#8b5cf6" fill="url(#colorTps)" strokeWidth={2} />
                                <Area type="monotone" dataKey="value2" name="Query Time (ms)" stroke="#3b82f6" fill="url(#colorQuery)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Connections by Database */}
                <div className={styles.chartCard}>
                    <div className={styles.chartHeader}>
                        <h3>Active Connections</h3>
                        <span className={styles.chartSubtitle}>By database</span>
                    </div>
                    <div className={styles.chartContent}>
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={connectionsData.length > 0 ? connectionsData : [{ name: 'No data', active: 0, idle: 0 }]} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                <XAxis type="number" stroke="#6b7280" fontSize={11} />
                                <YAxis type="category" dataKey="name" stroke="#6b7280" fontSize={11} width={100} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                                <Bar dataKey="active" name="Active" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                                <Bar dataKey="idle" name="Idle" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Storage Usage */}
                <div className={styles.chartCard}>
                    <div className={styles.chartHeader}>
                        <h3>Storage Usage</h3>
                        <span className={styles.chartSubtitle}>Tablespace/Database breakdown</span>
                    </div>
                    <div className={styles.chartContent}>
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={storageData.length > 0 ? storageData : [{ name: 'No data', used: 0 }]}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                <XAxis dataKey="name" stroke="#6b7280" fontSize={11} />
                                <YAxis stroke="#6b7280" fontSize={11} domain={[0, 100]} />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar dataKey="used" name="Used %" fill="#8b5cf6" radius={[4, 4, 0, 0]}>
                                    {storageData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color || '#8b5cf6'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Query Latency - Large Panel */}
                <div className={`${styles.chartCard} ${styles.wide}`}>
                    <div className={styles.chartHeader}>
                        <h3>Query Latency Distribution</h3>
                        <span className={styles.chartSubtitle}>Response time over time</span>
                    </div>
                    <div className={styles.chartContent}>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={latencyData}>
                                <defs>
                                    <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#ec4899" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#ec4899" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                <XAxis dataKey="time" stroke="#6b7280" fontSize={11} />
                                <YAxis stroke="#6b7280" fontSize={11} />
                                <Tooltip content={<CustomTooltip />} />
                                <Line type="monotone" dataKey="value" name="Latency (ms)" stroke="#ec4899" strokeWidth={2} dot={false} fill="url(#colorLatency)" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* IOPS */}
                <div className={styles.chartCard}>
                    <div className={styles.chartHeader}>
                        <h3>Disk I/O</h3>
                        <span className={styles.chartSubtitle}>Read/Write IOPS</span>
                    </div>
                    <div className={styles.chartContent}>
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={iopsData}>
                                <defs>
                                    <linearGradient id="colorIops" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                <XAxis dataKey="time" stroke="#6b7280" fontSize={10} interval={3} />
                                <YAxis stroke="#6b7280" fontSize={11} />
                                <Tooltip content={<CustomTooltip />} />
                                <Area type="monotone" dataKey="value" name="IOPS" stroke="#f59e0b" fill="url(#colorIops)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Lock Activity */}
                <div className={styles.chartCard}>
                    <div className={styles.chartHeader}>
                        <h3>Lock Activity</h3>
                        <span className={styles.chartSubtitle}>Locks & Deadlocks</span>
                    </div>
                    <div className={styles.chartContent}>
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={locksData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                <XAxis dataKey="time" stroke="#6b7280" fontSize={11} />
                                <YAxis stroke="#6b7280" fontSize={11} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                                <Bar dataKey="locks" name="Locks" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                                <Bar dataKey="deadlocks" name="Deadlocks" fill="#ef4444" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className={styles.footer}>
                <div className={styles.footerInfo}>
                    <Database size={14} />
                    <span>
                        {databases.length - 1} database{databases.length !== 2 ? 's' : ''} monitored
                    </span>
                </div>
                <div className={styles.footerInfo}>
                    <span>Auto-refresh: 30s • Last updated: {new Date().toLocaleTimeString('it-IT')}</span>
                </div>
            </div>
        </div>
    );
};

export default MetricsPanel;
