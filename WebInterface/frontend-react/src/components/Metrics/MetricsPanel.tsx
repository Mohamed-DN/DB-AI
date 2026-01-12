import React, { useState, useEffect } from 'react';
import { GrafanaDashboard } from './GrafanaDashboard';
import { MetricCard } from './MetricCard';
import styles from './MetricsPanel.module.css';

type ViewMode = 'overview' | 'capacity' | 'performance' | 'full';

// Mock data for demo (replace with real API calls)
const generateMockData = (points = 24) => {
    return Array.from({ length: points }, (_, i) => ({
        time: Date.now() - (points - i) * 3600000,
        value: Math.random() * 50 + 50
    }));
};

/**
 * MetricsPanel - Main metrics dashboard with tabs
 * Combines custom cards (overview) with embedded Grafana dashboards
 */
export const MetricsPanel: React.FC = () => {
    const [viewMode, setViewMode] = useState<ViewMode>('overview');
    const [metrics, setMetrics] = useState({
        bufferHit: { value: 98.5, data: generateMockData() },
        connections: { value: 42, data: generateMockData() },
        dbSize: { value: 156.8, data: generateMockData() },
        tps: { value: 1234, data: generateMockData() },
        queryTime: { value: 12.3, data: generateMockData() },
        alerts: { value: 3, data: generateMockData() }
    });

    // Auto-refresh metrics every 30s
    useEffect(() => {
        const interval = setInterval(() => {
            setMetrics(prev => ({
                bufferHit: { ...prev.bufferHit, value: 95 + Math.random() * 5 },
                connections: { ...prev.connections, value: Math.floor(30 + Math.random() * 30) },
                dbSize: { ...prev.dbSize, value: 150 + Math.random() * 20 },
                tps: { ...prev.tps, value: Math.floor(1000 + Math.random() * 500) },
                queryTime: { ...prev.queryTime, value: 5 + Math.random() * 20 },
                alerts: { ...prev.alerts, value: Math.floor(Math.random() * 5) }
            }));
        }, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <div className={styles.titleSection}>
                    <h1 className={styles.title}>📊 Database Metrics</h1>
                    <p className={styles.subtitle}>Real-time monitoring for PostgreSQL & Oracle</p>
                </div>

                {/* Tab Navigation */}
                <div className={styles.tabs}>
                    {(['overview', 'capacity', 'performance', 'full'] as ViewMode[]).map(mode => (
                        <button
                            key={mode}
                            className={`${styles.tab} ${viewMode === mode ? styles.active : ''}`}
                            onClick={() => setViewMode(mode)}
                        >
                            {mode === 'overview' && '📈'}
                            {mode === 'capacity' && '💾'}
                            {mode === 'performance' && '⚡'}
                            {mode === 'full' && '🖥️'}
                            <span>{mode.charAt(0).toUpperCase() + mode.slice(1)}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Content */}
            <div className={styles.content}>
                {/* Overview - Custom Metric Cards */}
                {viewMode === 'overview' && (
                    <>
                        <div className={styles.grid}>
                            <MetricCard
                                title="Buffer Hit Ratio"
                                value={metrics.bufferHit.value.toFixed(1)}
                                unit="%"
                                color="#10b981"
                                icon="🎯"
                                trend={metrics.bufferHit.value > 95 ? 'up' : 'down'}
                                chartData={metrics.bufferHit.data}
                            />
                            <MetricCard
                                title="Active Connections"
                                value={metrics.connections.value}
                                color="#8b5cf6"
                                icon="🔗"
                                trend="stable"
                                chartData={metrics.connections.data}
                            />
                            <MetricCard
                                title="Database Size"
                                value={metrics.dbSize.value.toFixed(1)}
                                unit="GB"
                                color="#f59e0b"
                                icon="💾"
                                trend="up"
                                chartData={metrics.dbSize.data}
                            />
                            <MetricCard
                                title="Transactions/sec"
                                value={metrics.tps.value.toLocaleString()}
                                unit="TPS"
                                color="#3b82f6"
                                icon="⚡"
                                trend="up"
                                chartData={metrics.tps.data}
                            />
                            <MetricCard
                                title="Avg Query Time"
                                value={metrics.queryTime.value.toFixed(1)}
                                unit="ms"
                                color="#ec4899"
                                icon="⏱️"
                                trend={metrics.queryTime.value < 15 ? 'up' : 'down'}
                                chartData={metrics.queryTime.data}
                            />
                            <MetricCard
                                title="Active Alerts"
                                value={metrics.alerts.value}
                                color={metrics.alerts.value > 0 ? '#ef4444' : '#10b981'}
                                icon="🚨"
                                trend={metrics.alerts.value === 0 ? 'up' : 'down'}
                                chartData={metrics.alerts.data}
                            />
                        </div>

                        {/* Quick Actions */}
                        <div className={styles.actions}>
                            <button className={styles.actionBtn} onClick={() => setViewMode('full')}>
                                🖥️ Open Full Dashboard
                            </button>
                            <a
                                href={`${import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3003'}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={styles.actionBtn}
                            >
                                🔗 Open Grafana
                            </a>
                        </div>
                    </>
                )}

                {/* Capacity Dashboard - Grafana Embed */}
                {viewMode === 'capacity' && (
                    <div className={styles.dashboardContainer}>
                        <GrafanaDashboard
                            dashboardUid="nexi-capacity"
                            theme="dark"
                            refresh="1m"
                            height="calc(100vh - 200px)"
                        />
                    </div>
                )}

                {/* Performance Dashboard - Grafana Embed */}
                {viewMode === 'performance' && (
                    <div className={styles.dashboardContainer}>
                        <GrafanaDashboard
                            dashboardUid="nexi-performance"
                            theme="dark"
                            refresh="30s"
                            height="calc(100vh - 200px)"
                        />
                    </div>
                )}

                {/* Full Dashboard */}
                {viewMode === 'full' && (
                    <div className={styles.dashboardContainer}>
                        <GrafanaDashboard
                            dashboardUid="nexi-overview"
                            theme="dark"
                            refresh="30s"
                            height="calc(100vh - 200px)"
                        />
                    </div>
                )}
            </div>
        </div>
    );
};

export default MetricsPanel;
