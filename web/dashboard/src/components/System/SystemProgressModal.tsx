import { useEffect, useRef } from 'react';
import { Check, X, Loader2, Terminal, AlertTriangle, Play, Pause } from 'lucide-react';

export interface ProgressEvent {
    type: 'start' | 'progress' | 'complete';
    action?: 'start' | 'stop';
    status?: string;
    container?: string;
    total?: number;
    success_count?: number;
    message?: string;
}

interface SystemProgressModalProps {
    isOpen: boolean;
    onClose: () => void;
    events: ProgressEvent[];
    isComplete: boolean;
    title: string;
}

export default function SystemProgressModal({ isOpen, onClose, events, isComplete, title }: SystemProgressModalProps) {
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom as new events arrive
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [events]);

    if (!isOpen) return null;

    // Calculate progress
    const startEvent = events.find(e => e.type === 'start');
    const total = startEvent?.total || 1;
    const completedCount = events.filter(e => e.type === 'progress' && (e.status === 'done' || e.status === 'failed')).length;
    const progressPercent = Math.min(100, Math.round((completedCount / total) * 100));

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <div className="glass w-full max-w-2xl flex flex-col max-h-[85vh] shadow-2xl animate-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="p-4 border-b border-white/10 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isComplete ? 'bg-emerald-500/20' : 'bg-blue-500/20'}`}>
                            {isComplete ? <Check className="w-5 h-5 text-emerald-400" /> : <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />}
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-white">{title}</h3>
                            <p className="text-sm text-gray-400">
                                {isComplete ? 'Operation completed' : `Processing containers (${completedCount}/${total})...`}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="h-2 bg-gray-800 w-full relative overflow-hidden">
                    <div
                        className={`absolute top-0 left-0 h-full transition-all duration-500 ${isComplete ? 'bg-emerald-500' : 'bg-blue-500'}`}
                        style={{ width: `${progressPercent}%` }}
                    ></div>
                </div>

                {/* Terminal / Log Output */}
                <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-2 font-mono text-sm bg-black/40 min-h-[300px]">
                    {events.length === 0 && (
                        <div className="text-gray-500 italic flex items-center gap-2">
                            <Loader2 className="w-3 h-3 animate-spin" /> Initializing connection...
                        </div>
                    )}

                    {events.map((event, idx) => {
                        if (event.type === 'start') return (
                            <div key={idx} className="text-cyan-400 pb-2 border-b border-white/5 mb-2">
                                🚀 Starting sequence: {event.action?.toUpperCase()} ({event.total} containers)
                            </div>
                        );

                        if (event.type === 'complete') return (
                            <div key={idx} className="text-emerald-400 pt-2 border-t border-white/5 mt-2 font-bold">
                                ✨ Sequence finished. Success: {event.success_count}/{event.total}
                            </div>
                        );

                        if (event.type === 'progress') {
                            if (event.status === 'pending') {
                                return (
                                    <div key={idx} className="text-yellow-500/80 flex items-center gap-2">
                                        <span className="w-1 h-1 bg-yellow-500 rounded-full"></span>
                                        {event.container}: {event.action}ing...
                                    </div>
                                )
                            } else if (event.status === 'done') {
                                return (
                                    <div key={idx} className="text-green-400 flex items-center gap-2 pl-4">
                                        <Check className="w-3 h-3" />
                                        {event.container}: Success
                                    </div>
                                )
                            } else {
                                return (
                                    <div key={idx} className="text-red-400 flex items-center gap-2 pl-4">
                                        <X className="w-3 h-3" />
                                        {event.container}: Failed ({event.message})
                                    </div>
                                )
                            }
                        }
                        return null;
                    })}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-white/10 flex justify-end">
                    <button
                        onClick={onClose}
                        disabled={!isComplete}
                        className={`btn-primary ${!isComplete ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {isComplete ? 'Close' : 'Please Wait...'}
                    </button>
                </div>
            </div>
        </div>
    );
}
