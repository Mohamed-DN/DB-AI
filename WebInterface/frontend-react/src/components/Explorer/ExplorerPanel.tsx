import { useState, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import * as api from '../../services/api';

export default function ExplorerPanel() {
    const [selectedCollection, setSelectedCollection] = useState('inventory_databases');
    const [selectedItem, setSelectedItem] = useState<any>(null);

    const { data: items, isLoading } = useQuery({
        queryKey: ['explorer', selectedCollection],
        queryFn: () => api.getRawCollection(selectedCollection),
    });

    const collections = [
        'inventory_databases',
        'monitoring_alerts',
        'business_services',
        'agent_config',
    ];

    const renderJsonTree = (data: any, depth = 0): ReactNode => {

        if (data === null) return <span className="text-gray-500">null</span>;
        if (typeof data === 'boolean') return <span className="text-purple-400">{String(data)}</span>;
        if (typeof data === 'number') return <span className="text-blue-400">{data}</span>;
        if (typeof data === 'string') return <span className="text-green-400">"{data}"</span>;

        if (Array.isArray(data)) {
            return (
                <div style={{ marginLeft: depth * 16 }}>
                    <span className="text-gray-400">[</span>
                    {data.map((item, i) => (
                        <div key={i} style={{ marginLeft: 16 }}>
                            {renderJsonTree(item, depth + 1)}
                            {i < data.length - 1 && <span className="text-gray-400">,</span>}
                        </div>
                    ))}
                    <span className="text-gray-400">]</span>
                </div>
            );
        }

        if (typeof data === 'object') {
            const keys = Object.keys(data);
            return (
                <div style={{ marginLeft: depth * 16 }}>
                    <span className="text-gray-400">{'{'}</span>
                    {keys.map((key, i) => (
                        <div key={key} style={{ marginLeft: 16 }}>
                            <span className="text-pink-400">"{key}"</span>
                            <span className="text-gray-400">: </span>
                            {renderJsonTree(data[key], depth + 1)}
                            {i < keys.length - 1 && <span className="text-gray-400">,</span>}
                        </div>
                    ))}
                    <span className="text-gray-400">{'}'}</span>
                </div>
            );
        }

        return <span>{String(data)}</span>;
    };

    return (
        <div className="flex gap-4 h-[600px]">
            {/* Sidebar */}
            <div className="w-72 glass overflow-y-auto">
                {/* Collection Selector */}
                <div className="p-4 border-b border-gray-700">
                    <select
                        value={selectedCollection}
                        onChange={(e) => {
                            setSelectedCollection(e.target.value);
                            setSelectedItem(null);
                        }}
                        className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2"
                    >
                        {collections.map((col) => (
                            <option key={col} value={col}>
                                {col}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Items List */}
                {isLoading ? (
                    <div className="p-4 text-gray-500">Loading...</div>
                ) : items && items.length > 0 ? (
                    items.map((item: any, index: number) => {
                        const title = item.identity?.db_unique_name || item.service || `Item ${index}`;
                        const sub = item._id || '';
                        return (
                            <div
                                key={item._id || index}
                                onClick={() => setSelectedItem(item)}
                                className={`p-4 border-b border-gray-700 cursor-pointer hover:bg-gray-700/30 ${selectedItem?._id === item._id ? 'bg-gray-700/50' : ''
                                    }`}
                            >
                                <h4 className="font-medium text-sm">{title}</h4>
                                <p className="text-xs text-gray-500 truncate">{sub}</p>
                            </div>
                        );
                    })
                ) : (
                    <div className="p-4 text-gray-500">No items found</div>
                )}
            </div>

            {/* Detail View */}
            <div className="flex-1 glass overflow-y-auto p-4">
                {selectedItem ? (
                    <div>
                        <h3 className="text-lg font-semibold mb-4">
                            {selectedItem.identity?.db_unique_name || 'Item Details'}
                        </h3>
                        <pre className="text-sm font-mono overflow-auto">
                            {renderJsonTree(selectedItem)}
                        </pre>
                    </div>
                ) : (
                    <div className="h-full flex items-center justify-center text-gray-500">
                        Select an item to view details
                    </div>
                )}
            </div>
        </div>
    );
}
