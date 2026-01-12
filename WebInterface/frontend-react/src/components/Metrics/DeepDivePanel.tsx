import React, { useState } from 'react';
import {
    BarChart3,
    HardDrive,
    Activity,
    AlertTriangle,
    RefreshCw,
    Timer
} from 'lucide-react';
import {
    AreaChart,
    Area,
    BarChart,
    Bar,
    Line,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
    ComposedChart
} from 'recharts';
import styles from './DeepDivePanel.module.css';

// ============================================================================
// MOCK DATA GENERATORS
// ============================================================================

// Generate time series data for the last N days
const generateDailyData = (days = 30, baseValue = 100, growthRate = 0.02) => {
    const now = Date.now();
    return Array.from({ length: days }, (_, i) => {
        const dayOffset = days - i;
        const growth = Math.pow(1 + growthRate, i);
        return {
            date: new Date(now - dayOffset * 86400000).toLocaleDateString('it-IT', { day: '2-digit', month: 'short' }),
            value: Math.round(baseValue * growth + (Math.random() - 0.5) * baseValue * 0.1),
            forecast: i > days - 7 ? Math.round(baseValue * growth * 1.1) : null
        };
    });
};

// Tablespace data with usage vs max
const tablespaceData = [
    { name: 'USERS', used: 78, max: 100, usedGB: 156, maxGB: 200, growthPerDay: 0.5 },
    { name: 'SYSTEM', used: 92, max: 100, usedGB: 46, maxGB: 50, growthPerDay: 0.1 },
    { name: 'SYSAUX', used: 67, max: 100, usedGB: 33.5, maxGB: 50, growthPerDay: 0.2 },
    { name: 'UNDOTBS1', used: 45, max: 100, usedGB: 22.5, maxGB: 50, growthPerDay: 0.8 },
    { name: 'TEMP', used: 35, max: 100, usedGB: 17.5, maxGB: 50, growthPerDay: 2.0 },
];

// PostgreSQL database sizes
const pgDatabaseData = generateDailyData(30, 50, 0.015).map((d, _i) => ({
    ...d,
    nexi_prod: d.value,
    nexi_dev: Math.round(d.value * 0.3),
    nexi_staging: Math.round(d.value * 0.5),
}));

// ASM Diskgroup data
const asmData = [
    { name: '+DATA', used: 72, total: 500, free: 140 },
    { name: '+RECO', used: 45, total: 200, free: 110 },
];

// I/O Performance data (hourly for last 24h)
const generateIOData = () => {
    return Array.from({ length: 24 }, (_, i) => ({
        time: `${String(i).padStart(2, '0')}:00`,
        readIOPS: 500 + Math.random() * 2000,
        writeIOPS: 200 + Math.random() * 800,
        readMBs: 50 + Math.random() * 150,
        writeMBs: 20 + Math.random() * 80,
    }));
};
const ioData = generateIOData();

// I/O Latency distribution
const latencyData = [
    { range: '< 1ms', sequential: 45, scattered: 20 },
    { range: '1-5ms', sequential: 30, scattered: 35 },
    { range: '5-10ms', sequential: 15, scattered: 25 },
    { range: '10-20ms', sequential: 7, scattered: 12 },
    { range: '> 20ms', sequential: 3, scattered: 8 },
];

// PostgreSQL cache stats
const cacheData = generateDailyData(24, 98.5, 0).map((_d, i) => ({
    time: `${String(i).padStart(2, '0')}:00`,
    hitRatio: 95 + Math.random() * 4.5,
    bufferHits: 10000 + Math.random() * 5000,
    diskReads: 100 + Math.random() * 500,
}));

// Checkpoint activity
const checkpointData = Array.from({ length: 24 }, (_, i) => ({
    time: `${String(i).padStart(2, '0')}:00`,
    checkpoint: 100 + Math.random() * 200,
    bgwriter: 50 + Math.random() * 100,
    backend: Math.random() > 0.8 ? Math.random() * 50 : 0, // Occasional backend writes (bad)
}));

// Resource limits
const resourceData = [
    { name: 'Processes', current: 245, limit: 300, pct: 82 },
    { name: 'Sessions', current: 380, limit: 500, pct: 76 },
    { name: 'Transactions', current: 0, limit: 0, pct: 0 },
];

// XID Age data
const xidData = [
    { name: 'nexi_prod', age: 450000000, pct: 22.5 },
    { name: 'nexi_dev', age: 120000000, pct: 6 },
    { name: 'nexi_staging', age: 280000000, pct: 14 },
];

// Temp usage over time
const tempData = Array.from({ length: 24 }, (_, i) => ({
    time: `${String(i).padStart(2, '0')}:00`,
    oracleTemp: 5 + Math.random() * 15,
    pgTemp: 2 + Math.random() * 8,
}));

// ============================================================================
// HELPER COMPONENTS
// ============================================================================

const GaugePanel: React.FC<{
    title: string;
    value: number;
    max?: number;
    unit?: string;
    thresholds?: { warning: number; critical: number };
}> = ({ title, value, max = 100, unit = '%', thresholds = { warning: 80, critical: 95 } }) => {
    const pct = (value / max) * 100;
    const color = pct >= thresholds.critical ? '#ef4444' : pct >= thresholds.warning ? '#f59e0b' : '#10b981';

    return (
        <div className={styles.gaugeCard}>
            <span className={styles.gaugeTitle}>{title}</span>
            <div className={styles.gaugeContainer}>
                <svg viewBox="0 0 100 60" className={styles.gaugeSvg}>
                    <path
                        d="M 10 55 A 40 40 0 0 1 90 55"
                        fill="none"
                        stroke="rgba(139, 92, 246, 0.2)"
                        strokeWidth="8"
                        strokeLinecap="round"
                    />
                    <path
                        d="M 10 55 A 40 40 0 0 1 90 55"
                        fill="none"
                        stroke={color}
                        strokeWidth="8"
                        strokeLinecap="round"
                        strokeDasharray={`${pct * 1.26} 126`}
                    />
                </svg>
                <div className={styles.gaugeValue} style={{ color }}>
                    {value.toFixed(1)}{unit}
                </div>
            </div>
        </div>
    );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export const DeepDivePanel: React.FC = () => {
    const [activeSection, setActiveSection] = useState<'storage' | 'io' | 'limits'>('storage');
    const [refreshing, setRefreshing] = useState(false);

    const handleRefresh = () => {
        setRefreshing(true);
        setTimeout(() => setRefreshing(false), 1000);
    };

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className={styles.tooltip}>
                    <p className={styles.tooltipLabel}>{label}</p>
                    {payload.map((entry: any, index: number) => (
                        <p key={index} style={{ color: entry.color }}>
                            {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    };

    // Calculate days until full for tablespaces
    const getDaysUntilFull = (ts: typeof tablespaceData[0]) => {
        const freeGB = ts.maxGB - ts.usedGB;
        return Math.round(freeGB / ts.growthPerDay);
    };

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <div className={styles.titleSection}>
                    <div className={styles.titleIcon}>
                        <BarChart3 size={24} />
                    </div>
                    <div>
                        <h1 className={styles.title}>Deep Dive Metrics</h1>
                        <p className={styles.subtitle}>Advanced database health & capacity analysis</p>
                    </div>
                </div>

                <div className={styles.controls}>
                    <div className={styles.sectionTabs}>
                        <button
                            className={`${styles.sectionTab} ${activeSection === 'storage' ? styles.active : ''}`}
                            onClick={() => setActiveSection('storage')}
                        >
                            <HardDrive size={16} />
                            Storage
                        </button>
                        <button
                            className={`${styles.sectionTab} ${activeSection === 'io' ? styles.active : ''}`}
                            onClick={() => setActiveSection('io')}
                        >
                            <Activity size={16} />
                            I/O & Latency
                        </button>
                        <button
                            className={`${styles.sectionTab} ${activeSection === 'limits' ? styles.active : ''}`}
                            onClick={() => setActiveSection('limits')}
                        >
                            <AlertTriangle size={16} />
                            Critical Limits
                        </button>
                    </div>
                    <button className={styles.refreshBtn} onClick={handleRefresh} disabled={refreshing}>
                        <RefreshCw size={16} className={refreshing ? styles.spinning : ''} />
                    </button>
                </div>
            </div>

            {/* ================================================================ */}
            {/* SECTION 1: STORAGE CAPACITY & GROWTH */}
            {/* ================================================================ */}
            {activeSection === 'storage' && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>
                        <HardDrive size={20} />
                        Storage Capacity & Growth Prediction
                    </h2>

                    <div className={styles.grid2}>
                        {/* Panel 1: Oracle Tablespace Utilization */}
                        <div className={styles.panel}>
                            <div className={styles.panelHeader}>
                                <h3>Oracle Tablespace Utilization</h3>
                                <span className={styles.panelSubtitle}>% of MAX_BYTES (autoextend-aware)</span>
                            </div>
                            <div className={styles.panelContent}>
                                <ResponsiveContainer width="100%" height={250}>
                                    <BarChart data={tablespaceData} layout="vertical">
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                        <XAxis type="number" domain={[0, 100]} stroke="#6b7280" fontSize={11} />
                                        <YAxis type="category" dataKey="name" stroke="#6b7280" fontSize={11} width={80} />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Bar dataKey="used" name="Used %" radius={[0, 4, 4, 0]}>
                                            {tablespaceData.map((entry, index) => (
                                                <Cell
                                                    key={`cell-${index}`}
                                                    fill={entry.used > 95 ? '#ef4444' : entry.used > 85 ? '#f59e0b' : '#10b981'}
                                                />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                                <div className={styles.legend}>
                                    <span className={styles.legendItem}><span style={{ background: '#10b981' }} /> &lt;85%</span>
                                    <span className={styles.legendItem}><span style={{ background: '#f59e0b' }} /> 85-95%</span>
                                    <span className={styles.legendItem}><span style={{ background: '#ef4444' }} /> &gt;95%</span>
                                </div>
                            </div>
                        </div>

                        {/* Panel 2: Growth Forecast */}
                        <div className={styles.panel}>
                            <div className={styles.panelHeader}>
                                <h3>Tablespace Growth Forecast</h3>
                                <span className={styles.panelSubtitle}>Days until capacity reached</span>
                            </div>
                            <div className={styles.panelContent}>
                                <div className={styles.forecastGrid}>
                                    {tablespaceData.map(ts => {
                                        const days = getDaysUntilFull(ts);
                                        const color = days < 7 ? '#ef4444' : days < 30 ? '#f59e0b' : '#10b981';
                                        return (
                                            <div key={ts.name} className={styles.forecastCard}>
                                                <span className={styles.forecastName}>{ts.name}</span>
                                                <span className={styles.forecastDays} style={{ color }}>
                                                    {days} <small>days</small>
                                                </span>
                                                <span className={styles.forecastGrowth}>
                                                    +{ts.growthPerDay} GB/day
                                                </span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className={styles.grid2}>
                        {/* Panel 3: PostgreSQL Database Growth */}
                        <div className={styles.panel}>
                            <div className={styles.panelHeader}>
                                <h3>PostgreSQL Database Growth</h3>
                                <span className={styles.panelSubtitle}>Size trend over 30 days</span>
                            </div>
                            <div className={styles.panelContent}>
                                <ResponsiveContainer width="100%" height={250}>
                                    <AreaChart data={pgDatabaseData}>
                                        <defs>
                                            <linearGradient id="colorProd" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4} />
                                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                            </linearGradient>
                                            <linearGradient id="colorDev" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                            </linearGradient>
                                            <linearGradient id="colorStg" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                                                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                        <XAxis dataKey="date" stroke="#6b7280" fontSize={10} interval={4} />
                                        <YAxis stroke="#6b7280" fontSize={11} />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Legend />
                                        <Area type="monotone" dataKey="nexi_prod" name="Production" stackId="1" stroke="#8b5cf6" fill="url(#colorProd)" />
                                        <Area type="monotone" dataKey="nexi_staging" name="Staging" stackId="1" stroke="#10b981" fill="url(#colorStg)" />
                                        <Area type="monotone" dataKey="nexi_dev" name="Development" stackId="1" stroke="#3b82f6" fill="url(#colorDev)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Panel 4: ASM Diskgroup Balance */}
                        <div className={styles.panel}>
                            <div className={styles.panelHeader}>
                                <h3>ASM Diskgroup Balance</h3>
                                <span className={styles.panelSubtitle}>Usage % per diskgroup</span>
                            </div>
                            <div className={styles.panelContent}>
                                <div className={styles.gaugeGrid}>
                                    {asmData.map(asm => (
                                        <GaugePanel
                                            key={asm.name}
                                            title={asm.name}
                                            value={asm.used}
                                            thresholds={{ warning: 80, critical: 90 }}
                                        />
                                    ))}
                                </div>
                                <div className={styles.asmDetails}>
                                    {asmData.map(asm => (
                                        <div key={asm.name} className={styles.asmDetail}>
                                            <span>{asm.name}</span>
                                            <span>{asm.total - (asm.total * asm.used / 100)} GB free</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* ================================================================ */}
            {/* SECTION 2: I/O & LATENCY ANALYSIS */}
            {/* ================================================================ */}
            {activeSection === 'io' && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>
                        <Activity size={20} />
                        Deep I/O & Latency Analysis
                    </h2>

                    <div className={styles.grid2}>
                        {/* Panel 5: Oracle I/O Performance */}
                        <div className={`${styles.panel} ${styles.wide}`}>
                            <div className={styles.panelHeader}>
                                <h3>Oracle Physical I/O Performance</h3>
                                <span className={styles.panelSubtitle}>IOPS & Throughput (Dual Y-Axis)</span>
                            </div>
                            <div className={styles.panelContent}>
                                <ResponsiveContainer width="100%" height={280}>
                                    <ComposedChart data={ioData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                        <XAxis dataKey="time" stroke="#6b7280" fontSize={11} />
                                        <YAxis yAxisId="left" stroke="#8b5cf6" fontSize={11} label={{ value: 'IOPS', angle: -90, position: 'insideLeft', fill: '#8b5cf6' }} />
                                        <YAxis yAxisId="right" orientation="right" stroke="#f59e0b" fontSize={11} label={{ value: 'MB/s', angle: 90, position: 'insideRight', fill: '#f59e0b' }} />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Legend />
                                        <Area yAxisId="left" type="monotone" dataKey="readIOPS" name="Read IOPS" stroke="#8b5cf6" fill="rgba(139, 92, 246, 0.2)" />
                                        <Area yAxisId="left" type="monotone" dataKey="writeIOPS" name="Write IOPS" stroke="#3b82f6" fill="rgba(59, 130, 246, 0.2)" />
                                        <Line yAxisId="right" type="monotone" dataKey="readMBs" name="Read MB/s" stroke="#f59e0b" strokeWidth={2} dot={false} />
                                        <Line yAxisId="right" type="monotone" dataKey="writeMBs" name="Write MB/s" stroke="#ec4899" strokeWidth={2} dot={false} />
                                    </ComposedChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    <div className={styles.grid2}>
                        {/* Panel 6: I/O Latency Distribution */}
                        <div className={styles.panel}>
                            <div className={styles.panelHeader}>
                                <h3>I/O Latency Distribution</h3>
                                <span className={styles.panelSubtitle}>Sequential vs Scattered reads</span>
                            </div>
                            <div className={styles.panelContent}>
                                <ResponsiveContainer width="100%" height={250}>
                                    <BarChart data={latencyData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                        <XAxis dataKey="range" stroke="#6b7280" fontSize={11} />
                                        <YAxis stroke="#6b7280" fontSize={11} />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Legend />
                                        <Bar dataKey="sequential" name="Sequential (single block)" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                                        <Bar dataKey="scattered" name="Scattered (full scan)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                                <div className={styles.latencyAlert}>
                                    <AlertTriangle size={14} color="#f59e0b" />
                                    <span>Warning: 8% of scattered reads &gt; 20ms</span>
                                </div>
                            </div>
                        </div>

                        {/* Panel 7: PostgreSQL Cache Hit Ratio */}
                        <div className={styles.panel}>
                            <div className={styles.panelHeader}>
                                <h3>PostgreSQL Cache Hit Ratio</h3>
                                <span className={styles.panelSubtitle}>Buffer Hits vs Disk Reads</span>
                            </div>
                            <div className={styles.panelContent}>
                                <div className={styles.cacheHeader}>
                                    <GaugePanel title="Hit Ratio" value={98.7} thresholds={{ warning: 95, critical: 90 }} />
                                </div>
                                <ResponsiveContainer width="100%" height={150}>
                                    <AreaChart data={cacheData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                        <XAxis dataKey="time" stroke="#6b7280" fontSize={10} interval={3} />
                                        <YAxis stroke="#6b7280" fontSize={11} />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Area type="monotone" dataKey="bufferHits" name="Buffer Hits" stroke="#10b981" fill="rgba(16, 185, 129, 0.3)" />
                                        <Area type="monotone" dataKey="diskReads" name="Disk Reads" stroke="#ef4444" fill="rgba(239, 68, 68, 0.3)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    {/* Panel 8: Checkpoint Activity */}
                    <div className={styles.panel}>
                        <div className={styles.panelHeader}>
                            <h3>Checkpoint & BGWriter Activity</h3>
                            <span className={styles.panelSubtitle}>Backend writes = bad (queries waiting on I/O)</span>
                        </div>
                        <div className={styles.panelContent}>
                            <ResponsiveContainer width="100%" height={220}>
                                <BarChart data={checkpointData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                    <XAxis dataKey="time" stroke="#6b7280" fontSize={11} />
                                    <YAxis stroke="#6b7280" fontSize={11} />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Legend />
                                    <Bar dataKey="checkpoint" name="Checkpoint" stackId="a" fill="#10b981" />
                                    <Bar dataKey="bgwriter" name="BGWriter" stackId="a" fill="#3b82f6" />
                                    <Bar dataKey="backend" name="Backend (⚠)" stackId="a" fill="#ef4444" />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>
            )}

            {/* ================================================================ */}
            {/* SECTION 3: CRITICAL LIMITS & HEALTH */}
            {/* ================================================================ */}
            {activeSection === 'limits' && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>
                        <AlertTriangle size={20} />
                        Critical Limits & Health
                    </h2>

                    <div className={styles.grid3}>
                        {/* Panel 9: Oracle Resource Limits */}
                        <div className={styles.panel}>
                            <div className={styles.panelHeader}>
                                <h3>Oracle Resource Limits</h3>
                                <span className={styles.panelSubtitle}>v$resource_limit</span>
                            </div>
                            <div className={styles.panelContent}>
                                <div className={styles.resourceGrid}>
                                    {resourceData.filter(r => r.limit > 0).map(r => (
                                        <div key={r.name} className={styles.resourceCard}>
                                            <span className={styles.resourceName}>{r.name}</span>
                                            <div className={styles.resourceBar}>
                                                <div
                                                    className={styles.resourceFill}
                                                    style={{
                                                        width: `${r.pct}%`,
                                                        background: r.pct > 90 ? '#ef4444' : r.pct > 80 ? '#f59e0b' : '#10b981'
                                                    }}
                                                />
                                            </div>
                                            <span className={styles.resourceValue}>{r.current} / {r.limit}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Panel 10: XID Wraparound */}
                        <div className={styles.panel}>
                            <div className={styles.panelHeader}>
                                <h3>PostgreSQL XID Wraparound</h3>
                                <span className={styles.panelSubtitle}>Distance to 2B limit</span>
                            </div>
                            <div className={styles.panelContent}>
                                <div className={styles.xidGrid}>
                                    {xidData.map(db => (
                                        <div key={db.name} className={styles.xidCard}>
                                            <span className={styles.xidName}>{db.name}</span>
                                            <GaugePanel
                                                title=""
                                                value={db.pct}
                                                max={100}
                                                thresholds={{ warning: 50, critical: 75 }}
                                            />
                                            <span className={styles.xidAge}>
                                                {(db.age / 1000000).toFixed(0)}M XIDs
                                            </span>
                                        </div>
                                    ))}
                                </div>
                                <div className={styles.xidWarning}>
                                    <AlertTriangle size={14} />
                                    <span>Autovacuum freeze at 200M. Emergency at 2B.</span>
                                </div>
                            </div>
                        </div>

                        {/* Panel 11: Temp Space Usage */}
                        <div className={styles.panel}>
                            <div className={styles.panelHeader}>
                                <h3>Temp Space Usage</h3>
                                <span className={styles.panelSubtitle}>Disk sorts indicator</span>
                            </div>
                            <div className={styles.panelContent}>
                                <ResponsiveContainer width="100%" height={200}>
                                    <AreaChart data={tempData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                        <XAxis dataKey="time" stroke="#6b7280" fontSize={10} interval={3} />
                                        <YAxis stroke="#6b7280" fontSize={11} unit=" GB" />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Legend />
                                        <Area type="monotone" dataKey="oracleTemp" name="Oracle TEMP" stroke="#f59e0b" fill="rgba(245, 158, 11, 0.3)" />
                                        <Area type="monotone" dataKey="pgTemp" name="PG temp_bytes" stroke="#8b5cf6" fill="rgba(139, 92, 246, 0.3)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    {/* Alert Summary */}
                    <div className={styles.alertSummary}>
                        <h3>Active Alerts</h3>
                        <div className={styles.alertList}>
                            <div className={`${styles.alertItem} ${styles.warning}`}>
                                <AlertTriangle size={16} />
                                <span>SYSTEM tablespace at 92% - 50 days until full</span>
                            </div>
                            <div className={`${styles.alertItem} ${styles.info}`}>
                                <Timer size={16} />
                                <span>Process utilization at 82% - monitor closely</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DeepDivePanel;
