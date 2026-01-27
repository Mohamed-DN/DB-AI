
import { Activity } from 'lucide-react';

export default function SystemStatus() {
    return (
        <div className="p-4 bg-gray-800 rounded-lg">
            <div className="flex items-center gap-2 mb-4">
                <Activity className="w-5 h-5 text-blue-400" />
                <h2 className="text-lg font-semibold text-white">System Status</h2>
            </div>
            <div className="text-gray-400">
                Status monitoring active...
            </div>
        </div>
    );
}
