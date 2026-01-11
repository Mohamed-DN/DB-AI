import { Bot } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function SettingsPanel() {
    const navigate = useNavigate();

    return (
        <div className="glass p-12 text-center flex flex-col items-center justify-center min-h-[400px]">
            <div className="p-4 rounded-full bg-purple-500/20 mb-6 animate-pulse">
                <Bot className="w-16 h-16 text-purple-400" />
            </div>

            <h2 className="text-2xl font-bold mb-4">Settings Moved</h2>
            <p className="text-gray-400 max-w-md mx-auto mb-8">
                Agent configuration, including intervals and start/stop controls, has been moved to the new consolidated <strong>Agents Panel</strong>.
            </p>

            <button
                onClick={() => navigate('/agents')}
                className="btn-primary px-8 py-3 text-lg flex items-center gap-2"
            >
                <Bot className="w-5 h-5" />
                Go to Agents Configuration
            </button>
        </div>
    );
}
