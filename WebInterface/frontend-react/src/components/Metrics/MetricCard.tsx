import React from 'react';
import {
    AreaChart,
    Area,
    Tooltip,
    ResponsiveContainer
} from 'recharts';
import styles from './MetricCard.module.css';

interface MetricCardProps {
    title: string;
    value?: string | number;
    unit?: string;
    color?: string;
    icon?: React.ReactNode;
    trend?: 'up' | 'down' | 'stable';
    chartData?: { time: number; value: number }[];
    showChart?: boolean;
    loading?: boolean;
}

/**
 * MetricCard - Displays a metric with optional sparkline chart
 */
export const MetricCard: React.FC<MetricCardProps> = ({
    title,
    value = '--',
    unit = '',
    color = '#8b5cf6',
    icon,
    trend,
    chartData = [],
    showChart = true,
    loading = false
}) => {
    const trendIcon = trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→';
    const trendColor = trend === 'up' ? '#10b981' : trend === 'down' ? '#ef4444' : '#6b7280';

    return (
        <div className={styles.card}>
            <div className={styles.header}>
                <div className={styles.titleRow}>
                    {icon && <span className={styles.icon}>{icon}</span>}
                    <span className={styles.title}>{title}</span>
                </div>
                {trend && (
                    <span className={styles.trend} style={{ color: trendColor }}>
                        {trendIcon}
                    </span>
                )}
            </div>

            <div className={styles.valueRow}>
                <span className={styles.value} style={{ color }}>
                    {loading ? '...' : value}
                </span>
                <span className={styles.unit}>{unit}</span>
            </div>

            {showChart && chartData.length > 0 && (
                <div className={styles.chart}>
                    <ResponsiveContainer width="100%" height={60}>
                        <AreaChart data={chartData}>
                            <defs>
                                <linearGradient id={`gradient-${title.replace(/\s/g, '')}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor={color} stopOpacity={0.4} />
                                    <stop offset="100%" stopColor={color} stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <Area
                                type="monotone"
                                dataKey="value"
                                stroke={color}
                                fill={`url(#gradient-${title.replace(/\s/g, '')})`}
                                strokeWidth={2}
                            />
                            <Tooltip
                                contentStyle={{
                                    background: 'rgba(20, 20, 40, 0.95)',
                                    border: '1px solid rgba(139, 92, 246, 0.3)',
                                    borderRadius: 8,
                                    fontSize: 12
                                }}
                                labelFormatter={(label) => new Date(label).toLocaleTimeString()}
                                formatter={(val) => [typeof val === 'number' ? val.toFixed(2) : String(val), title]}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
};

export default MetricCard;
