import React, { useState } from 'react';
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
import styles from './MetricsPanel.module.css';

/**
 * MetricsPanel - Comprehensive database metrics dashboard
 * Integrates Grafana panels with native UI components
 */
export const MetricsPanel: React.FC = () => {
    const [selectedDb, setSelectedDb] = useState<string>('all');
    const [timeRange, setTimeRange] = useState<string>('24h');
    const [refreshing, setRefreshing] = useState(false);

    const grafanaUrl = import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3003';

    // Time range options
    const timeRanges = [
        { label: '1h', value: '1h' },
        { label: '6h', value: '6h' },
        { label: '24h', value: '24h' },
        { label: '7d', value: '7d' },
        { label: '30d', value: '30d' },
    ];

    // Database filter options
    const databases = [
        { label: 'All Databases', value: 'all' },
        { label: 'PostgreSQL Milano', value: 'pg-milano' },
        { label: 'PostgreSQL Bratislava', value: 'pg-bratislava' },
        { label: 'Oracle Cairo', value: 'oracle-cairo' },
    ];

    const handleRefresh = () => {
        setRefreshing(true);
        setTimeout(() => setRefreshing(false), 1000);
    };

    // Build Grafana embed URL with parameters
    const getGrafanaPanel = (panelId: number, height = 300) => {
        const from = `now-${timeRange}`;
        return `${grafanaUrl}/d-solo/nexi-overview?orgId=1&panelId=${panelId}&from=${from}&to=now&theme=dark&refresh=30s`;
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
                    {/* Database Filter */}
                    <select
                        className={styles.select}
                        value={selectedDb}
                        onChange={(e) => setSelectedDb(e.target.value)}
                    >
                        {databases.map(db => (
                            <option key={db.value} value={db.value}>{db.label}</option>
                        ))}
                    </select>

                    {/* Time Range */}
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

                    {/* Refresh Button */}
                    <button
                        className={styles.refreshBtn}
                        onClick={handleRefresh}
                        disabled={refreshing}
                    >
                        <RefreshCw size={16} className={refreshing ? styles.spinning : ''} />
                    </button>

                    {/* Open Grafana */}
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
                        <span className={styles.statValue}>98.7%</span>
                        <span className={styles.statLabel}>Buffer Hit</span>
                    </div>
                    <TrendingUp size={16} className={styles.trendUp} />
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon} style={{ background: 'rgba(139, 92, 246, 0.15)' }}>
                        <Zap size={20} color="#8b5cf6" />
                    </div>
                    <div className={styles.statContent}>
                        <span className={styles.statValue}>1,247</span>
                        <span className={styles.statLabel}>TPS</span>
                    </div>
                    <TrendingUp size={16} className={styles.trendUp} />
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon} style={{ background: 'rgba(245, 158, 11, 0.15)' }}>
                        <HardDrive size={20} color="#f59e0b" />
                    </div>
                    <div className={styles.statContent}>
                        <span className={styles.statValue}>156.8 GB</span>
                        <span className={styles.statLabel}>Total Size</span>
                    </div>
                    <TrendingUp size={16} className={styles.trendUp} />
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon} style={{ background: 'rgba(59, 130, 246, 0.15)' }}>
                        <Server size={20} color="#3b82f6" />
                    </div>
                    <div className={styles.statContent}>
                        <span className={styles.statValue}>42</span>
                        <span className={styles.statLabel}>Connections</span>
                    </div>
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon} style={{ background: 'rgba(236, 72, 153, 0.15)' }}>
                        <Clock size={20} color="#ec4899" />
                    </div>
                    <div className={styles.statContent}>
                        <span className={styles.statValue}>12.3 ms</span>
                        <span className={styles.statLabel}>Avg Query</span>
                    </div>
                </div>

                <div className={styles.statCard}>
                    <div className={styles.statIcon} style={{ background: 'rgba(239, 68, 68, 0.15)' }}>
                        <AlertTriangle size={20} color="#ef4444" />
                    </div>
                    <div className={styles.statContent}>
                        <span className={styles.statValue}>2</span>
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
                        <span className={styles.chartSubtitle}>TPS, Query Time, Buffer Hit</span>
                    </div>
                    <div className={styles.chartContent}>
                        <iframe
                            src={getGrafanaPanel(1)}
                            className={styles.grafanaFrame}
                            title="Performance Overview"
                        />
                    </div>
                </div>

                {/* Connections */}
                <div className={styles.chartCard}>
                    <div className={styles.chartHeader}>
                        <h3>Active Connections</h3>
                        <span className={styles.chartSubtitle}>By database</span>
                    </div>
                    <div className={styles.chartContent}>
                        <iframe
                            src={getGrafanaPanel(2)}
                            className={styles.grafanaFrame}
                            title="Connections"
                        />
                    </div>
                </div>

                {/* Storage Usage */}
                <div className={styles.chartCard}>
                    <div className={styles.chartHeader}>
                        <h3>Storage Usage</h3>
                        <span className={styles.chartSubtitle}>Tablespace breakdown</span>
                    </div>
                    <div className={styles.chartContent}>
                        <iframe
                            src={getGrafanaPanel(3)}
                            className={styles.grafanaFrame}
                            title="Storage"
                        />
                    </div>
                </div>

                {/* Query Latency Heatmap - Large Panel */}
                <div className={`${styles.chartCard} ${styles.wide}`}>
                    <div className={styles.chartHeader}>
                        <h3>Query Latency Distribution</h3>
                        <span className={styles.chartSubtitle}>Response time heatmap</span>
                    </div>
                    <div className={styles.chartContent}>
                        <iframe
                            src={getGrafanaPanel(4)}
                            className={styles.grafanaFrame}
                            title="Query Latency"
                        />
                    </div>
                </div>

                {/* IOPS */}
                <div className={styles.chartCard}>
                    <div className={styles.chartHeader}>
                        <h3>Disk I/O</h3>
                        <span className={styles.chartSubtitle}>Read/Write IOPS</span>
                    </div>
                    <div className={styles.chartContent}>
                        <iframe
                            src={getGrafanaPanel(5)}
                            className={styles.grafanaFrame}
                            title="IOPS"
                        />
                    </div>
                </div>

                {/* Lock Activity */}
                <div className={styles.chartCard}>
                    <div className={styles.chartHeader}>
                        <h3>Lock Activity</h3>
                        <span className={styles.chartSubtitle}>Locks & Deadlocks</span>
                    </div>
                    <div className={styles.chartContent}>
                        <iframe
                            src={getGrafanaPanel(6)}
                            className={styles.grafanaFrame}
                            title="Locks"
                        />
                    </div>
                </div>
            </div>

            {/* Footer Info */}
            <div className={styles.footer}>
                <div className={styles.footerInfo}>
                    <Database size={14} />
                    <span>Data refreshes every 30 seconds</span>
                </div>
                <div className={styles.footerInfo}>
                    <span>Powered by Prometheus + Grafana</span>
                </div>
            </div>
        </div>
    );
};

export default MetricsPanel;
