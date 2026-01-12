import React, { useState } from 'react';
import { MetricsPanel } from './MetricsPanel';
import { DeepDivePanel } from './DeepDivePanel';
import { BarChart3, Microscope } from 'lucide-react';
import styles from './MetricsContainer.module.css';

type ViewMode = 'overview' | 'deepdive';

/**
 * MetricsContainer - Wrapper component that allows switching between
 * Overview (MetricsPanel) and Deep Dive (DeepDivePanel) views
 */
export const MetricsContainer: React.FC = () => {
    const [viewMode, setViewMode] = useState<ViewMode>('overview');

    return (
        <div className={styles.container}>
            {/* View Toggle */}
            <div className={styles.toggleBar}>
                <button
                    className={`${styles.toggleBtn} ${viewMode === 'overview' ? styles.active : ''}`}
                    onClick={() => setViewMode('overview')}
                >
                    <BarChart3 size={16} />
                    <span>Overview</span>
                </button>
                <button
                    className={`${styles.toggleBtn} ${viewMode === 'deepdive' ? styles.active : ''}`}
                    onClick={() => setViewMode('deepdive')}
                >
                    <Microscope size={16} />
                    <span>Deep Dive</span>
                </button>
            </div>

            {/* Content */}
            <div className={styles.content}>
                {viewMode === 'overview' ? <MetricsPanel /> : <DeepDivePanel />}
            </div>
        </div>
    );
};

export default MetricsContainer;
