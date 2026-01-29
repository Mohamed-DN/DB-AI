import { Terminal, SquareTerminal, Trash2, ChevronDown, ChevronUp, Database, RefreshCw, Loader, Search, Layers, ChevronRight, ChevronLeft } from 'lucide-react';
import { useState, useMemo } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useDatabases, useDeleteDatabase } from '../../hooks/useDatabases';
import { useConnection } from '../../context/ConnectionContext';
import type { Database as DatabaseType, PDB } from '../../types/database';

function StatusBadge({ status }: { status: string }) {
    const statusClasses: Record<string, string> = {
        UP: 'status-up',
        DOWN: 'status-down',
        WARNING: 'status-warning',
        UNKNOWN: 'bg-gray-500/20 text-gray-400 border border-gray-500/30',
        MISSING: 'bg-gray-500/20 text-gray-400 border border-gray-500/30',
    };

    return (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusClasses[status] || statusClasses.UNKNOWN}`}>
            {status}
        </span>
    );
}

function PDBRow({ pdb, parentDb }: { pdb: PDB; parentDb: DatabaseType }) {
    const { connect } = useConnection();

    const handleConnect = () => {
        const pdbPath = `${parentDb.identity.db_unique_name}/${pdb.name}`;
        connect(pdbPath, 'sql');
    };

    return (
        <tr className="table-row bg-gray-900/30">
            <td className="px-6 py-3">
                <StatusBadge status={pdb.status === 'NORMAL' || pdb.status === 'READ WRITE' ? 'UP' : 'WARNING'} />
            </td>
            <td className="px-6 py-3">
                <div className="flex items-center gap-2 pl-8">
                    <Database className="w-4 h-4 text-purple-400" />
                    <span className="text-purple-300">{pdb.name}</span>
                    <span className="text-xs text-gray-500">PDB</span>
                </div>
            </td>
            <td className="px-6 py-3 text-gray-500">{parentDb.connection?.host || parentDb.identity?.host || 'N/A'}</td>
            <td className="px-6 py-3 text-gray-500">{parentDb.connection?.port ?? 'N/A'}</td>
            <td className="px-6 py-3 text-gray-500">{parentDb.identity?.environment || 'N/A'}</td>
            <td className="px-6 py-3">
                <span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded text-xs">
                    {pdb.status}
                </span>
            </td>
            <td className="px-6 py-3">
                <button
                    onClick={handleConnect}
                    className="btn-secondary text-sm"
                    title="Connect to PDB"
                >
                    <Terminal className="w-4 h-4" />
                    Connect
                </button>
            </td>
        </tr>
    );
}

function DatabaseRow({ db }: { db: DatabaseType }) {
    const [expanded, setExpanded] = useState(false);
    const { connect } = useConnection();
    const deleteMutation = useDeleteDatabase();

    const pdbs = db.pdbs || db.configuration?.oracle_specific?.pdbs || [];
    const hasPdbs = pdbs.length > 0;
    const service = (db as any).business_service;

    const handleSqlConnect = () => {
        connect(db.identity.db_unique_name, 'sql');
    };

    const handleBashConnect = () => {
        connect(db.identity.db_unique_name, 'bash');
    };

    const handleDelete = () => {
        if (confirm(`Delete ${db.identity.db_unique_name}?`)) {
            deleteMutation.mutate(db.identity.db_unique_name);
        }
    };

    return (
        <>
            <tr className={`table-row ${expanded ? 'bg-gray-800/60 transition-colors' : ''}`}>
                <td className="px-6 py-4">
                    <StatusBadge status={db.state?.status || 'UNKNOWN'} />
                </td>
                <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                        <button onClick={() => setExpanded(!expanded)} className="text-gray-400 hover:text-white transition-colors">
                            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>
                        <span className="font-medium">{db.identity.db_unique_name}</span>
                        <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">
                            {db.identity.topology}
                        </span>
                    </div>
                </td>
                <td className="px-6 py-4">
                    <span className={`flex items-center gap-2 ${db.identity.engine === 'ORACLE' ? 'text-red-400' : 'text-blue-400'}`}>
                        <Database className="w-4 h-4" />
                        {db.identity.engine}
                    </span>
                </td>
                <td className="px-6 py-4 text-gray-400">
                    {db.connection?.host || db.identity?.host || 'N/A'}
                </td>
                <td className="px-6 py-4 text-gray-400">
                    {db.connection?.port ?? 'N/A'}
                </td>
                <td className="px-6 py-4 text-gray-400">
                    {db.identity.environment || 'N/A'}
                </td>
                <td className="px-6 py-4">
                    <div className="flex gap-2">
                        <button
                            onClick={() => connect(db.identity.db_unique_name, 'sysdba')}
                            className="p-2 bg-yellow-500/20 text-yellow-400 rounded hover:bg-yellow-500/30 transition-colors"
                            title={db.identity.engine === 'ORACLE' ? 'SYSDBA Mode' : 'Superuser (postgres)'}
                        >
                            <span className="text-xs font-bold">{db.identity.engine === 'ORACLE' ? 'DBA' : 'SU'}</span>
                        </button>
                        <button
                            onClick={handleSqlConnect}
                            className="p-2 bg-green-500/20 text-green-400 rounded hover:bg-green-500/30 transition-colors"
                            title="SQL Console (AIAUTO)"
                        >
                            <Terminal className="w-4 h-4" />
                        </button>
                        <button
                            onClick={handleBashConnect}
                            className="p-2 bg-cyan-500/20 text-cyan-400 rounded hover:bg-cyan-500/30 transition-colors"
                            title="Bash Shell"
                        >
                            <SquareTerminal className="w-4 h-4" />
                        </button>
                        <button
                            onClick={handleDelete}
                            className="p-2 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition-colors"
                            title="Delete"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                </td>
            </tr>
            {expanded && (
                <tr className="bg-gray-900/30">
                    <td colSpan={7} className="px-6 py-4">
                        <div className="grid grid-cols-3 gap-8 text-sm">
                            <div className="space-y-2">
                                <h4 className="text-gray-400 font-semibold uppercase text-xs tracking-wider mb-2">Business Census</h4>
                                <div className="grid grid-cols-[100px_1fr] gap-1">
                                    <span className="text-gray-500">Service:</span>
                                    <span className="text-gray-300">{service?.name || "N/A"}</span>
                                    <span className="text-gray-500">SNOW Group:</span>
                                    <span className="text-cyan-400 font-mono text-xs">{service?.snow_group || "UNASSIGNED"}</span>
                                    <span className="text-gray-500">On-call:</span>
                                    <span className="text-orange-400">{service?.reperibility || "N/A"}</span>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <h4 className="text-gray-400 font-semibold uppercase text-xs tracking-wider mb-2">Technical Census</h4>
                                <div className="grid grid-cols-[100px_1fr] gap-1">
                                    <span className="text-gray-500">Gateway:</span>
                                    <span className="text-purple-400 font-mono text-xs">{db.identity.gateway_ref || "DIRECT/UNKNOWN"}</span>
                                    <span className="text-gray-500">Version:</span>
                                    <span className="text-gray-300">{db.configuration?.version || "Unknown"}</span>
                                    <span className="text-gray-500">OS:</span>
                                    <span className="text-gray-300">{(db.state.metrics as any)?.os?.name || "Linux"}</span>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <h4 className="text-gray-400 font-semibold uppercase text-xs tracking-wider mb-2">Capacity & Policy</h4>
                                <div className="grid grid-cols-[100px_1fr] gap-1">
                                    <span className="text-gray-500">Storage:</span>
                                    <span className="text-gray-300">{(db.state.metrics as any)?.disk_io || "N/A"}</span>
                                </div>
                            </div>
                        </div>

                        {hasPdbs && (
                            <div className="mt-4 pt-4 border-t border-gray-700/50">
                                <h4 className="text-gray-400 font-semibold uppercase text-xs tracking-wider mb-2">Pluggable Databases (PDBs)</h4>
                                <table className="w-full text-sm">
                                    <tbody>
                                        {pdbs.map((pdb) => (
                                            <PDBRow key={pdb.name} pdb={pdb} parentDb={db} />
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </td>
                </tr>
            )}
        </>
    );
}

function GatewayGroup({ gateway, dbs }: { gateway: string, dbs: DatabaseType[] }) {
    const [open, setOpen] = useState(true);
    const onlineCount = dbs.filter(d => d.state?.status === 'UP').length;

    return (
        <div className="border-b border-gray-800">
            <button
                onClick={() => setOpen(!open)}
                className="w-full px-6 py-3 bg-gray-900/50 hover:bg-gray-800/80 transition-colors flex items-center justify-between group"
            >
                <div className="flex items-center gap-3">
                    <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${open ? '' : '-rotate-90'}`} />
                    <span className="font-semibold text-gray-200">{gateway || "Direct / Unknown"}</span>
                    <span className="px-2 py-0.5 rounded-full bg-gray-800 text-xs text-gray-400 group-hover:bg-gray-700">
                        {dbs.length} DBs
                    </span>
                </div>
                <div className="flex items-center gap-4 text-xs font-mono">
                    <span className="text-green-400">{onlineCount} UP</span>
                    <span className="text-gray-600">|</span>
                    <span className="text-red-400">{dbs.length - onlineCount} DOWN</span>
                </div>
            </button>
            {open && (
                <div className="border-t border-gray-800">
                    <table className="w-full">
                        <thead className="bg-gray-900/20 text-xs uppercase text-gray-500">
                            <tr>
                                <th className="px-6 py-2 text-left">Status</th>
                                <th className="px-6 py-2 text-left">Name</th>
                                <th className="px-6 py-2 text-left">Engine</th>
                                <th className="px-6 py-2 text-left">Host</th>
                                <th className="px-6 py-2 text-left">Port</th>
                                <th className="px-6 py-2 text-left">Env</th>
                                <th className="px-6 py-2 text-left">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-gray-900/10">
                            {dbs.map(db => <DatabaseRow key={db._id} db={db} />)}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

export default function InventoryTable() {
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [startsWith, setStartsWith] = useState('');
    const [filterBy, setFilterBy] = useState('name'); // 'name' or 'host'
    const [grouped, setGrouped] = useState(false);

    // Using corrected useDatabases hook
    const { data, isLoading, error } = useDatabases(page, search, startsWith, filterBy);
    const queryClient = useQueryClient();
    const [isRefreshing, setIsRefreshing] = useState(false);

    // Handle both array (legacy) and InventoryResponse object
    const items = Array.isArray(data) ? data : (data?.items || []);
    const total = Array.isArray(data) ? data.length : (data?.total || 0);
    const totalPages = Math.ceil(total / 1000) || 1;

    // Grouping Logic
    const groupedData = useMemo(() => {
        if (!grouped || !items) return {};
        return items.reduce((acc, db) => {
            const gw = db.identity.gateway_ref || "Unknown";
            if (!acc[gw]) acc[gw] = [];
            acc[gw].push(db);
            return acc;
        }, {} as Record<string, DatabaseType[]>);
    }, [items, grouped]);

    const handleRefresh = async () => {
        setIsRefreshing(true);
        try {
            await fetch('/api/action/collect', { method: 'POST' });
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['databases'] });
                setIsRefreshing(false);
            }, 2000);
        } catch (e) {
            console.error("Refresh failed", e);
            setIsRefreshing(false);
        }
    };

    const handleLetterClick = (letter: string) => {
        if (startsWith === letter) {
            setStartsWith(''); // Toggle off
        } else {
            setStartsWith(letter);
            setSearch(''); // Clear text search if using index
            setPage(1);
        }
    };

    const alphabet = "#ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

    if (isLoading) {
        return (
            <div className="glass p-8 text-center text-gray-400">
                <Loader className="w-8 h-8 mx-auto mb-4 animate-spin text-blue-500" />
                <p>Loading Inventory...</p>
            </div>
        );
    }

    if (error) {
        return <div className="glass p-8 text-center text-red-400">Error loading inventory</div>;
    }

    return (
        <div className="glass overflow-hidden flex flex-col">
            {/* Toolbar */}
            <div className="p-4 bg-gray-900/40 border-b border-white/5 flex flex-col gap-4">

                <div className="flex flex-wrap items-center justify-between gap-4">
                    <div className="flex items-center gap-3 flex-1 min-w-[200px]">
                        <div className="relative flex-1 max-w-md">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                            <input
                                type="text"
                                placeholder="Search DB, Host, IP..."
                                className="bg-black/20 border border-white/10 rounded-lg pl-9 pr-4 py-2 text-sm w-full focus:outline-none focus:border-blue-500/50 transition-colors text-white"
                                value={search}
                                onChange={(e) => { setSearch(e.target.value); setStartsWith(''); setPage(1); }}
                            />
                        </div>

                        <div className="flex bg-black/20 rounded-lg p-1 border border-white/10">
                            <button
                                onClick={() => setFilterBy('name')}
                                className={`px-3 py-1 rounded text-xs transition-colors ${filterBy === 'name' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
                            >
                                Name
                            </button>
                            <button
                                onClick={() => setFilterBy('host')}
                                className={`px-3 py-1 rounded text-xs transition-colors ${filterBy === 'host' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
                            >
                                Host
                            </button>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setGrouped(!grouped)}
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm border transition-colors ${grouped ? 'bg-blue-500/20 border-blue-500/50 text-blue-400' : 'bg-transparent border-white/10 text-gray-400 hover:text-white'}`}
                        >
                            <Layers className="w-4 h-4" />
                            Group by Gateway
                        </button>

                        <div className="h-6 w-px bg-white/10 mx-1" />

                        <button
                            onClick={handleRefresh}
                            disabled={isRefreshing}
                            className={`p-2 hover:bg-white/5 rounded-lg transition-colors ${isRefreshing ? 'animate-spin text-blue-400' : 'text-gray-400'}`}
                        >
                            {isRefreshing ? <Loader className="w-4 h-4" /> : <RefreshCw className="w-4 h-4" />}
                        </button>
                    </div>
                </div>

                {/* Alphabet Filter */}
                <div className="flex flex-wrap gap-1 px-1">
                    {alphabet.map(letter => (
                        <button
                            key={letter}
                            onClick={() => handleLetterClick(letter === '#' ? '' : letter)}
                            className={`w-8 h-8 flex items-center justify-center rounded text-xs font-mono transition-colors ${startsWith === letter ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' : 'bg-gray-800/50 text-gray-400 hover:bg-gray-700 hover:text-white'}`}
                        >
                            {letter}
                        </button>
                    ))}
                </div>
            </div>

            {/* Content */}
            <div className="overflow-x-auto min-h-[400px]">
                {items.length === 0 ? (
                    <div className="p-12 text-center text-gray-500">
                        <Database className="w-12 h-12 mx-auto mb-4 opacity-20" />
                        <p>No databases found matching your search.</p>
                    </div>
                ) : grouped ? (
                    // Grouped View
                    <div className="divide-y divide-gray-800">
                        {Object.entries(groupedData).map(([gw, dbs]) => (
                            <GatewayGroup key={gw} gateway={gw} dbs={dbs} />
                        ))}
                    </div>
                ) : (
                    // Table View
                    <table className="w-full">
                        <thead className="bg-gray-800/50">
                            <tr>
                                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Name</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Engine</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Host</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Port</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Env</th>
                                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800/50">
                            {items.map((db) => (
                                <DatabaseRow key={db._id} db={db} />
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Pagination Footer */}
            <div className="p-4 bg-gray-900/40 border-t border-white/5 flex items-center justify-between text-sm">
                <span className="text-gray-500">
                    Showing {items.length} of {total} databases
                </span>

                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="p-1 rounded hover:bg-white/5 disabled:opacity-30 disabled:hover:bg-transparent"
                    >
                        <ChevronLeft className="w-5 h-5 text-gray-400" />
                    </button>
                    <span className="text-gray-300">Page {page} of {totalPages}</span>
                    <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page >= totalPages}
                        className="p-1 rounded hover:bg-white/5 disabled:opacity-30 disabled:hover:bg-transparent"
                    >
                        <ChevronRight className="w-5 h-5 text-gray-400" />
                    </button>
                </div>
            </div>
        </div>
    );
}
