import React from 'react';
import styles from './GrafanaDashboard.module.css';

interface GrafanaDashboardProps {
    dashboardUid: string;
    panelId?: number;
    from?: string;
    to?: string;
    theme?: 'light' | 'dark';
    refresh?: string;
    height?: string;
}

/**
 * GrafanaDashboard - Embeds Grafana dashboards or panels via iframe
 * 
 * Usage:
 *   <GrafanaDashboard dashboardUid="m-dn-capacity" />
 *   <GrafanaDashboard dashboardUid="m-dn-main" panelId={2} />
 */
export const GrafanaDashboard: React.FC<GrafanaDashboardProps> = ({
    dashboardUid,
    panelId,
    from = 'now-24h',
    to = 'now',
    theme = 'dark',
    refresh = '30s',
    height = '600px'
}) => {
    const grafanaUrl = import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3003';

    // Full dashboard or single panel
    const embedUrl = panelId
        ? `${grafanaUrl}/d-solo/${dashboardUid}?panelId=${panelId}&from=${from}&to=${to}&theme=${theme}&refresh=${refresh}`
        : `${grafanaUrl}/d/${dashboardUid}?kiosk&from=${from}&to=${to}&theme=${theme}&refresh=${refresh}`;

    return (
        <div className={styles.container} style={{ height }}>
            <iframe
                src={embedUrl}
                className={styles.iframe}
                frameBorder="0"
                title="Grafana Dashboard"
                allow="fullscreen"
            />
        </div>
    );
};

export default GrafanaDashboard;
