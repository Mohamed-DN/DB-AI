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

    const renderJsonTree = (data: any, depth = 0, isLast = true): ReactNode => {

        if (data === null) return <span className="text-gray-500">null</span>;
        if (typeof data === 'boolean') return <span className="text-purple-400">{String(data)}</span>;
        if (typeof data === 'number') return <span className="text-blue-400">{data}</span>;
        if (typeof data === 'string') return <span className="text-green-400">"{data}"</span>;

        const indentStyle = { paddingLeft: 16, borderLeft: '1px solid #374151', marginLeft: 4 };

        if (Array.isArray(data)) {
            return (
                <div className="relative">
                    <span className="text-gray-500 text-xs">Array[{data.length}]</span>
                    <div style={indentStyle}>
                        {data.map((item, i) => (
                            <div key={i} className="relative py-1">
                                <span className="absolute -left-4 top-4 w-4 h-[1px] bg-gray-700"></span>
                                {renderJsonTree(item, depth + 1, i === data.length - 1)}
                            </div>
                        ))}
                    </div>
                </div>
            );
        }

        if (typeof data === 'object') {
            const keys = Object.keys(data);
            return (
                <div className="relative">
                    <div style={indentStyle}>
                        {keys.map((key, i) => (
                            <div key={key} className="relative py-1">
                                <span className="absolute -left-4 top-4 w-4 h-[1px] bg-gray-700"></span>
                                <span className="text-pink-400 font-semibold text-xs mr-2">{key}:</span>
                                {renderJsonTree(data[key], depth + 1, i === keys.length - 1)}
                            </div>
                        ))}
                    </div>
                </div>
            );
        }

        return <span className="bg-gray-800/50 px-1 rounded text-gray-300">{String(data)}</span>;
    };

    // Ref for JSON Crack iframe
    const jsonCrackRef = import.meta.env.MODE === 'development' ? null : null; // irrelevant, just placeholder logic if needed

    // We use a callback ref or simple effect to handle postMessage
    const handleIframeLoad = (e: React.SyntheticEvent<HTMLIFrameElement>) => {
        const iframe = e.currentTarget;
        if (selectedItem) {
            iframe.contentWindow?.postMessage({
                json: JSON.stringify(selectedItem)
            }, "*");
        }
    };

    // Update graph when selected item changes
    const [iframeRef, setIframeRef] = useState<HTMLIFrameElement | null>(null);

    if (selectedItem && iframeRef?.contentWindow) {
        iframeRef.contentWindow.postMessage({
            json: JSON.stringify(selectedItem)
        }, "*");
    }

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

            {/* Detail Panel */}
            <div className="flex-1 glass p-4 overflow-y-auto">
                {selectedItem ? (
                    <div>
                        <h3 className="text-lg font-semibold mb-4">
                            {selectedItem.identity?.db_unique_name || 'Item Details'}
                        </h3>
                        <pre className="text-sm font-mono overflow-auto h-[200px] mb-4 border-b border-gray-700 pb-4">
                            {renderJsonTree(selectedItem)}
                        </pre>

                        {/* JSON Crack Embed */}
                        <div className="h-[500px] bg-[#2d3142] rounded overflow-hidden flex flex-col">
                            <div className="p-2 bg-gray-800/50 text-xs text-gray-400 flex justify-between">
                                <span>Graphical View (JSON Crack)</span>
                                <span>Powered by jsoncrack.com</span>
                            </div>
                            <iframe
                                ref={setIframeRef}
                                className="w-full flex-1 border-0"
                                src="https://jsoncrack.com/widget"
                                onLoad={handleIframeLoad}
                                title="JSON Crack"
                            />
                        </div>
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

