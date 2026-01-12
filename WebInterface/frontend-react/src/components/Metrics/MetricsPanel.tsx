import React, { useState, useEffect } from 'react';
import {
    BarChart3,
    Activity,
    HardDrive,
    Zap,
    Database,
    RefreshCw,
    ExternalLink,
    TrendingUp,
    Clock,
    AlertTriangle,
    Server
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
import styles from './MetricsPanel.module.css';

// Generate mock time series data
const generateTimeData = (hours = 24, baseValue = 50, variance = 20) => {
    const now = Date.now();
    return Array.from({ length: hours }, (_, i) => ({
        time: new Date(now - (hours - i) * 3600000).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }),
        value: Math.max(0, baseValue + (Math.random() - 0.5) * variance * 2),
        value2: Math.max(0, baseValue * 0.8 + (Math.random() - 0.5) * variance * 2),
    }));
};

// Mock data for charts
const performanceData = generateTimeData(24, 1200, 300);
const connectionsData = [
    { name: 'PG Milano', active: 18, idle: 12, color: '#8b5cf6' },
    { name: 'PG Bratislava', active: 8, idle: 6, color: '#3b82f6' },
    { name: 'Oracle Cairo', active: 14, idle: 10, color: '#f59e0b' },
];
const storageData = [
    { name: 'USERS', used: 78, free: 22, color: '#10b981' },
    { name: 'SYSTEM', used: 92, free: 8, color: '#ef4444' },
    { name: 'TEMP', used: 45, free: 55, color: '#8b5cf6' },
    { name: 'UNDO', used: 64, free: 36, color: '#3b82f6' },
];
const latencyData = generateTimeData(24, 15, 10);
const iopsData = generateTimeData(24, 500, 200);
const locksData = [
    { time: '00:00', locks: 2, deadlocks: 0 },
    { time: '04:00', locks: 1, deadlocks: 0 },
    { time: '08:00', locks: 5, deadlocks: 1 },
    { time: '12:00', locks: 8, deadlocks: 0 },
    { time: '16:00', locks: 12, deadlocks: 2 },
    { time: '20:00', locks: 6, deadlocks: 0 },
];


/**
 * MetricsPanel - Database metrics dashboard with native Recharts
 */
export const MetricsPanel: React.FC = () => {
    const [selectedDb, setSelectedDb] = useState<string>('all');
    const [timeRange, setTimeRange] = useState<string>('24h');
    const [refreshing, setRefreshing] = useState(false);
    const [metrics, setMetrics] = useState({
        bufferHit: 98.7,
        tps: 1247,
        storage: 156.8,
        connections: 42,
        queryTime: 12.3,
        alerts: 2
    });

    const grafanaUrl = import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3003';

    const timeRanges = [
        { label: '1h', value: '1h' },
        { label: '6h', value: '6h' },
        { label: '24h', value: '24h' },
        { label: '7d', value: '7d' },
        { label: '30d', value: '30d' },
    ];

    const databases = [
        { label: 'All Databases', value: 'all' },
        { label: 'PostgreSQL Milano', value: 'pg-milano' },
        { label: 'PostgreSQL Bratislava', value: 'pg-bratislava' },
        { label: 'Oracle Cairo', value: 'oracle-cairo' },
    ];

    const handleRefresh = () => {
        setRefreshing(true);
        // Simulate data refresh
        setTimeout(() => {
            setMetrics({
                bufferHit: 95 + Math.random() * 5,
                tps: 1000 + Math.floor(Math.random() * 500),
                storage: 150 + Math.random() * 20,
                connections: 30 + Math.floor(Math.random() * 30),
                queryTime: 5 + Math.random() * 20,
                alerts: Math.floor(Math.random() * 5)
            });
            setRefreshing(false);
        }, 1000);
    };

    // Auto-refresh every 30s
    useEffect(() => {
        const interval = setInterval(handleRefresh, 30000);
        return () => clearInterval(interval);
    }, []);

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
                        <p className={styles.subtitle}>Real-time performance monitoring for all databases</p>
                    </div>
                </div>

                {/* Controls */}
                <div className={styles.controls}>
                    <select
                        className={styles.select}
                        value={selectedDb}
                        onChange={(e) => setSelectedDb(e.target.value)}
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
                    >
                        <RefreshCw size={16} className={refreshing ? styles.spinning : ''} />
                    </button>

                    <a
                        href={grafanaUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.externalBtn}
                    >
                        <ExternalLink size={16} />
                        <span>Open Grafana</span>
                    </a>
                </div>
            </div>

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
                            <BarChart data={connectionsData} layout="vertical">
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
                        <span className={styles.chartSubtitle}>Tablespace breakdown</span>
                    </div>
                    <div className={styles.chartContent}>
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={storageData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                <XAxis dataKey="name" stroke="#6b7280" fontSize={11} />
                                <YAxis stroke="#6b7280" fontSize={11} domain={[0, 100]} />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar dataKey="used" name="Used %" fill="#8b5cf6" radius={[4, 4, 0, 0]}>
                                    {storageData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.used > 90 ? '#ef4444' : entry.used > 80 ? '#f59e0b' : '#10b981'} />
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
                    <span>Data refreshes every 30 seconds</span>
                </div>
                <div className={styles.footerInfo}>
                    <span>Native Charts • No Grafana Required</span>
                </div>
            </div>
        </div>
    );
};

export default MetricsPanel;
