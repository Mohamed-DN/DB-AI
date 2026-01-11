import { Terminal, SquareTerminal, Trash2, ChevronDown, ChevronUp, Database, RefreshCw, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useDatabases, useConnectDatabase, useDeleteDatabase } from '../../hooks/useDatabases';
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
    const connectMutation = useConnectDatabase();

    const handleConnect = () => {
        const pdbPath = `${parentDb.identity.db_unique_name}/${pdb.name}`;
        connectMutation.mutate({ dbName: pdbPath, mode: 'sql' });
    };

    return (
        <tr className="table-row bg-gray-900/30">
            <td className="px-6 py-3">
                <StatusBadge status={pdb.status === 'NORMAL' || pdb.status === 'READ WRITE' ? 'UP' : 'WARNING'} />
            </td>
            <td className="px-6 py-3">
                <div className="flex items-center gap-2 pl-8">
                    <Database className="w-4 h-4 text-purple-400" />
                    <span className="text-purple-300">↳ {pdb.name}</span>
                    <span className="text-xs text-gray-500">PDB</span>
                </div>
            </td>
            <td className="px-6 py-3 text-gray-500">—</td>
            <td className="px-6 py-3 text-gray-500">—</td>
            <td className="px-6 py-3 text-gray-500">—</td>
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
    const connectMutation = useConnectDatabase();
    const deleteMutation = useDeleteDatabase();

    const pdbs = db.pdbs || db.configuration?.oracle_specific?.pdbs || [];
    const hasPdbs = pdbs.length > 0;
    const service = (db as any).business_service; // Type assertion until types updated

    const handleSqlConnect = () => {
        connectMutation.mutate({ dbName: db.identity.db_unique_name, mode: 'sql' });
    };

    const handleBashConnect = () => {
        connectMutation.mutate({ dbName: db.identity.db_unique_name, mode: 'bash' });
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
                    {db.connection?.port || '—'}
                </td>
                <td className="px-6 py-4 text-gray-400">
                    {db.identity.environment || 'N/A'}
                </td>
                <td className="px-6 py-4">
                    <div className="flex gap-2">
                        <button
                            onClick={() => connectMutation.mutate({ dbName: db.identity.db_unique_name, mode: 'sysdba' })}
                            className="p-2 bg-yellow-500/20 text-yellow-400 rounded hover:bg-yellow-500/30 transition-colors"
                            title="SYSDBA / Superuser"
                        >
                            <span className="text-xs font-bold">DBA</span>
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
                            {/* Census / Ownership */}
                            <div className="space-y-2">
                                <h4 className="text-gray-400 font-semibold uppercase text-xs tracking-wider mb-2">Business Census</h4>
                                <div className="grid grid-cols-[100px_1fr] gap-1">
                                    <span className="text-gray-500">Service:</span>
                                    <span className="text-gray-300">{service?.name || "N/A"}</span>

                                    <span className="text-gray-500">SNOW Group:</span>
                                    <span className="text-cyan-400 font-mono text-xs">{service?.snow_group || "UNASSIGNED"}</span>

                                    <span className="text-gray-500">Reperibilità:</span>
                                    <span className="text-orange-400">{service?.reperibility || "N/A"}</span>

                                    <span className="text-gray-500">BAO:</span>
                                    <div className="flex flex-col">
                                        <span className="text-white">{service?.contacts?.bao?.name || "Unknown"}</span>
                                        <span className="text-xs text-gray-500">{service?.contacts?.bao?.email}</span>
                                        <span className="text-xs text-gray-500">{service?.contacts?.bao?.phone}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Technical Details */}
                            <div className="space-y-2">
                                <h4 className="text-gray-400 font-semibold uppercase text-xs tracking-wider mb-2">Technical Census</h4>
                                <div className="grid grid-cols-[100px_1fr] gap-1">
                                    <span className="text-gray-500">Version:</span>
                                    <span className="text-gray-300">{db.configuration?.version || "Unknown"}</span>

                                    <span className="text-gray-500">Gateway:</span>
                                    <span className="text-gray-300">{db.identity.gateway_ref || "Direct"}</span>

                                    <span className="text-gray-500">OS:</span>
                                    <span className="text-gray-300">{(db.state.metrics as any)?.os?.name || "Linux"}</span>

                                    <span className="text-gray-500">Licensing:</span>
                                    <span className="text-purple-400">Standard Edition</span>
                                </div>
                            </div>

                            {/* Capacity / Other */}
                            <div className="space-y-2">
                                <h4 className="text-gray-400 font-semibold uppercase text-xs tracking-wider mb-2">Capacity & Policy</h4>
                                <div className="grid grid-cols-[100px_1fr] gap-1">
                                    <span className="text-gray-500">Storage:</span>
                                    <span className="text-gray-300">{(db.state.metrics as any)?.disk_io || "N/A"} (Current)</span>

                                    <span className="text-gray-500">Max Size:</span>
                                    <span className="text-gray-300">Not Set</span>

                                    <span className="text-gray-500">Retention:</span>
                                    <span className="text-gray-300">30 Days (Default)</span>
                                </div>
                            </div>
                        </div>

                        {/* PDB List */}
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

export default function InventoryTable() {
    const { data: databases, isLoading, error } = useDatabases();

    if (isLoading) {
        return (
            <div className="glass p-8">
                <div className="animate-pulse space-y-4">
                    {[...Array(5)].map((_, i) => (
                        <div key={i} className="h-12 bg-gray-800 rounded"></div>
                    ))}
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="glass p-8 text-center text-red-400">
                Error loading inventory
            </div>
        );
    }

    const queryClient = useQueryClient();
    const [isRefreshing, setIsRefreshing] = useState(false);

    const handleRefresh = async () => {
        setIsRefreshing(true);
        try {
            await fetch('/api/action/collect', { method: 'POST' });
            // Wait 2 seconds for Collector to perform its check
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['databases'] });
                setIsRefreshing(false);
            }, 2000);
        } catch (e) {
            console.error("Refresh failed", e);
            setIsRefreshing(false);
        }
    };

    return (
        <div className="glass overflow-hidden">
            <table className="w-full">
                <thead className="bg-gray-800/50">
                    <tr>
                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider flex items-center gap-2">
                            Status
                            <button
                                onClick={handleRefresh}
                                disabled={isRefreshing}
                                title="Force Refresh Status"
                                className={`hover:text-white transition-colors ${isRefreshing ? 'animate-spin text-blue-400' : ''}`}
                            >
                                {isRefreshing ? <Loader2 className="w-4 h-4" /> : <RefreshCw className="w-4 h-4" />}
                            </button>
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Name</th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Engine</th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Host</th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Port</th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Env</th>
                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {databases?.map((db) => (
                        <DatabaseRow key={db._id} db={db} />
                    ))}
                </tbody>
            </table>
        </div>
    );
}
