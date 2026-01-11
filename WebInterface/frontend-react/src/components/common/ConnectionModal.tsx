import { useState, useEffect } from 'react';
import { Database, Loader2, CheckCircle, XCircle, Terminal, X } from 'lucide-react';

interface ConnectionModalProps {
    isOpen: boolean;
    onClose: () => void;
    dbName: string;
    mode: 'sql' | 'bash' | 'sysdba';
    status: 'connecting' | 'success' | 'error';
    message?: string;
}

const modeLabels = {
    sql: 'SQL Console',
    bash: 'Bash Shell',
    sysdba: 'SYSDBA Mode'
};

const modeColors = {
    sql: 'text-green-400',
    bash: 'text-cyan-400',
    sysdba: 'text-yellow-400'
};

export default function ConnectionModal({ isOpen, onClose, dbName, mode, status, message }: ConnectionModalProps) {
    const [step, setStep] = useState(0);
    const [dots, setDots] = useState('');

    // Animated dots
    useEffect(() => {
        if (status === 'connecting') {
            const interval = setInterval(() => {
                setDots(prev => prev.length >= 3 ? '' : prev + '.');
            }, 400);
            return () => clearInterval(interval);
        }
    }, [status]);

    // Connection steps animation
    useEffect(() => {
        if (status === 'connecting') {
            const steps = [
                { delay: 0, step: 0 },
                { delay: 800, step: 1 },
                { delay: 1600, step: 2 },
                { delay: 2400, step: 3 }
            ];

            steps.forEach(({ delay, step: s }) => {
                setTimeout(() => setStep(s), delay);
            });
        }
    }, [status]);

    if (!isOpen) return null;

    const connectionSteps = [
        'Resolving gateway...',
        'Establishing SSH tunnel...',
        'Authenticating credentials...',
        'Opening session...'
    ];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                onClick={status !== 'connecting' ? onClose : undefined}
            />

            {/* Modal */}
            <div className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl border border-gray-700/50 shadow-2xl w-[420px] overflow-hidden">
                {/* Header gradient bar */}
                <div className={`h-1 ${status === 'error' ? 'bg-red-500' : status === 'success' ? 'bg-green-500' : 'bg-gradient-to-r from-purple-500 via-blue-500 to-cyan-500'}`} />

                {/* Close button */}
                {status !== 'connecting' && (
                    <button
                        onClick={onClose}
                        className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                )}

                <div className="p-8">
                    {/* Database icon with animation */}
                    <div className="flex justify-center mb-6">
                        <div className={`relative ${status === 'connecting' ? 'animate-pulse' : ''}`}>
                            {status === 'connecting' ? (
                                <div className="relative">
                                    <Database className="w-20 h-20 text-purple-500" />
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <Loader2 className="w-10 h-10 text-cyan-400 animate-spin" />
                                    </div>
                                    {/* Orbiting dots */}
                                    <div className="absolute inset-0 animate-spin" style={{ animationDuration: '3s' }}>
                                        <div className="absolute top-0 left-1/2 w-2 h-2 bg-purple-500 rounded-full transform -translate-x-1/2 -translate-y-2" />
                                    </div>
                                    <div className="absolute inset-0 animate-spin" style={{ animationDuration: '2s', animationDirection: 'reverse' }}>
                                        <div className="absolute bottom-0 left-1/2 w-2 h-2 bg-cyan-500 rounded-full transform -translate-x-1/2 translate-y-2" />
                                    </div>
                                </div>
                            ) : status === 'success' ? (
                                <CheckCircle className="w-20 h-20 text-green-500" />
                            ) : (
                                <XCircle className="w-20 h-20 text-red-500" />
                            )}
                        </div>
                    </div>

                    {/* Title */}
                    <h2 className="text-xl font-bold text-center text-white mb-2">
                        {status === 'connecting' ? 'Connecting' : status === 'success' ? 'Connected!' : 'Connection Failed'}
                        {status === 'connecting' && <span className="text-gray-400">{dots}</span>}
                    </h2>

                    {/* Database name */}
                    <p className="text-center text-gray-400 mb-1">
                        <Terminal className={`inline w-4 h-4 mr-2 ${modeColors[mode]}`} />
                        <span className={modeColors[mode]}>{modeLabels[mode]}</span>
                    </p>
                    <p className="text-center font-mono text-sm text-purple-400 mb-6">
                        {dbName}
                    </p>

                    {/* Connection steps */}
                    {status === 'connecting' && (
                        <div className="space-y-2 mb-6">
                            {connectionSteps.map((stepText, i) => (
                                <div
                                    key={i}
                                    className={`flex items-center gap-3 text-sm transition-all duration-300 ${i < step ? 'text-green-400' :
                                            i === step ? 'text-white' :
                                                'text-gray-600'
                                        }`}
                                >
                                    {i < step ? (
                                        <CheckCircle className="w-4 h-4 text-green-400" />
                                    ) : i === step ? (
                                        <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
                                    ) : (
                                        <div className="w-4 h-4 rounded-full border border-gray-600" />
                                    )}
                                    <span>{stepText}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Status message */}
                    {message && status !== 'connecting' && (
                        <p className={`text-center text-sm ${status === 'error' ? 'text-red-400' : 'text-gray-400'}`}>
                            {message}
                        </p>
                    )}

                    {/* Success message */}
                    {status === 'success' && (
                        <p className="text-center text-green-400 text-sm">
                            Terminal window opened successfully!
                        </p>
                    )}

                    {/* Action button */}
                    {status !== 'connecting' && (
                        <button
                            onClick={onClose}
                            className={`w-full mt-6 py-3 rounded-lg font-medium transition-all ${status === 'success'
                                    ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                                    : 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                                }`}
                        >
                            {status === 'success' ? 'Done' : 'Close'}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
