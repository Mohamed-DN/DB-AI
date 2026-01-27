import { Server, Terminal } from 'lucide-react';
import { useDatabases } from '../../hooks/useDatabases';
import { useConnection } from '../../context/ConnectionContext';

interface Host {
    name: string;
    os: string;
    cpu: string | number;
    mem: number;
    dbs: string[];
}

const GENERIC_NAMES = ['localhost', '127.0.0.1', 'mongodb', 'postgres', 'mysql', 'oracle', 'redis', 'mariadb', 'mssql'];

const isGeneric = (name: string) => {
    if (!name) return true;
    return GENERIC_NAMES.includes(name.toLowerCase());
};

export default function HostsTable() {
    const { data: databases, isLoading } = useDatabases();
    const { connect } = useConnection();

    // Extract unique hosts from databases
    const hosts: Host[] = [];
    const hostMap: Record<string, Host> = {};

    if (databases) {
        databases.forEach((db: any) => {
            // Prioritize Container Name or DB Unique Name over Metrics Hostname
            // Avoid generic names like "mongodb" or "postgres", preferring specific names like "nexi-cmdb-mongo"
            const candidates = [
                db.connection?.container,
                db.identity?.db_unique_name,
                db.state?.metrics?.hostname,
                db.connection?.host
            ].filter(Boolean);

            // Find first non-generic candidate
            let hostname = candidates.find(c => !isGeneric(c));

            // Fallback to first generic candidate if no specific one found
            if (!hostname && candidates.length > 0) {
                hostname = candidates[0];
            }

            if (!hostname) return;

            if (!hostMap[hostname]) {
                hostMap[hostname] = {
                    name: hostname,
                    os: db.state?.metrics?.os?.name || 'Linux (Container)',
                    cpu: db.state?.metrics?.cpu?.cores || 'Shared',
                    mem: db.state?.metrics?.memory?.total_gb || 0,
                    dbs: [],
                };
            }
            // Avoid duplicate DB names in the list
            const dbName = db.identity?.db_unique_name || 'Unknown';
            if (!hostMap[hostname].dbs.includes(dbName)) {
                hostMap[hostname].dbs.push(dbName);
            }
        });

        Object.values(hostMap).forEach((h) => hosts.push(h));
    }

    if (isLoading) {
        return <div className="glass p-8 text-center text-gray-500">Loading hosts...</div>;
    }

    return (
        <div className="glass overflow-hidden">
            <table className="w-full">
                <thead>
                    <tr className="border-b border-gray-700">
                        <th className="text-left p-4 text-gray-400 text-sm">Hostname / IP</th>
                        <th className="text-left p-4 text-gray-400 text-sm">OS Info</th>
                        <th className="text-left p-4 text-gray-400 text-sm">Resources</th>
                        <th className="text-left p-4 text-gray-400 text-sm">Databases</th>
                        <th className="text-left p-4 text-gray-400 text-sm">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {hosts.map((host) => (
                        <tr key={host.name} className="table-row">
                            <td className="p-4">
                                <div className="flex items-center gap-2">
                                    <Server className="w-4 h-4 text-blue-400" />
                                    <span className="font-medium">{host.name}</span>
                                </div>
                            </td>
                            <td className="p-4 text-gray-400">{host.os}</td>
                            <td className="p-4 text-gray-400">
                                {host.cpu} Cores / {typeof host.mem === 'number' ? host.mem.toFixed(1) : host.mem} GB RAM
                            </td>
                            <td className="p-4">
                                <div className="flex flex-wrap gap-1">
                                    {host.dbs.map((db) => (
                                        <span
                                            key={db}
                                            className="text-xs bg-gray-700/50 px-2 py-1 rounded"
                                        >
                                            {db}
                                        </span>
                                    ))}
                                </div>
                            </td>
                            <td className="p-4">
                                <button
                                    onClick={() => connect(host.dbs[0] || host.name, 'bash')}
                                    className="btn-secondary text-sm"
                                >
                                    <Terminal className="w-3 h-3" />
                                    SSH
                                </button>
                            </td>
                        </tr>
                    ))}
                    {hosts.length === 0 && (
                        <tr>
                            <td colSpan={5} className="p-8 text-center text-gray-500">
                                No hosts found
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}
