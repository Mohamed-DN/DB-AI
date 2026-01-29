import { useEffect, useState, useRef } from 'react';
import { Search, Monitor, Database, Terminal, Settings, ArrowRight } from 'lucide-react';
import { createPortal } from 'react-dom';

interface CommandPaletteProps {
    isOpen: boolean;
    onClose: () => void;
    onNavigate: (tab: string) => void;
}

export default function CommandPalette({ isOpen, onClose, onNavigate }: CommandPaletteProps) {
    const [query, setQuery] = useState('');
    const [selectedIndex, setSelectedIndex] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);

    // Command List (Mock for now, can be dynamic)
    const allCommands = [
        { id: 'dashboard', label: 'Go to Dashboard', icon: Monitor, group: 'Navigation' },
        { id: 'inventory', label: 'Go to Inventory', icon: Database, group: 'Navigation' },
        { id: 'alerts', label: 'Go to Alerts', icon: Terminal, group: 'Navigation' },
        { id: 'monitoring', label: 'Go to Monitoring', icon: Monitor, group: 'Navigation' },
        { id: 'settings', label: 'Go to Settings', icon: Settings, group: 'Navigation' },
        { id: 'db-1', label: 'View Database: CRM_PROD', icon: Database, group: 'Databases' },
        { id: 'db-2', label: 'View Database: BILLING_DB', icon: Database, group: 'Databases' },
        { id: 'oem-1', label: 'View OEM: NEXI_OEM_01', icon: Monitor, group: 'OEM Instances' },
    ];

    const filteredCommands = allCommands.filter(cmd =>
        cmd.label.toLowerCase().includes(query.toLowerCase())
    );

    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 50);
        } else {
            setQuery('');
            setSelectedIndex(0);
        }
    }, [isOpen]);

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (!isOpen) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setSelectedIndex(prev => (prev + 1) % filteredCommands.length);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setSelectedIndex(prev => (prev - 1 + filteredCommands.length) % filteredCommands.length);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (filteredCommands[selectedIndex]) {
                    handleSelect(filteredCommands[selectedIndex]);
                }
            } else if (e.key === 'Escape') {
                onClose();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, filteredCommands, selectedIndex]);

    const handleSelect = (cmd: any) => {
        if (cmd.group === 'Navigation') {
            onNavigate(cmd.id);
        } else {
            console.log("Selected:", cmd.label);
            // Implement specific navigation or action logic here
        }
        onClose();
    };

    if (!isOpen) return null;

    return createPortal(
        <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[20vh] px-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative w-full max-w-2xl bg-gray-900 border border-gray-700 rounded-xl shadow-2xl overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">

                {/* Search Input */}
                <div className="flex items-center px-4 py-4 border-b border-gray-800">
                    <Search className="w-5 h-5 text-gray-500 mr-3" />
                    <input
                        ref={inputRef}
                        type="text"
                        className="flex-1 bg-transparent border-none outline-none text-lg text-white placeholder-gray-500 font-medium"
                        placeholder="Type a command or search..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <span className="text-xs font-mono text-gray-500 border border-gray-700 rounded px-1.5 py-0.5">ESC</span>
                </div>

                {/* Results */}
                <div className="max-h-[60vh] overflow-y-auto py-2">
                    {filteredCommands.length === 0 ? (
                        <div className="px-4 py-8 text-center text-gray-500">
                            No results found for "{query}"
                        </div>
                    ) : (
                        filteredCommands.map((cmd, index) => (
                            <button
                                key={cmd.id}
                                onClick={() => handleSelect(cmd)}
                                className={`w-full flex items-center px-4 py-3 text-left transition-colors
                            ${index === selectedIndex ? 'bg-blue-600/10 border-l-2 border-blue-500' : 'hover:bg-gray-800 border-l-2 border-transparent'}
                        `}
                            >
                                <cmd.icon className={`w-5 h-5 mr-3 ${index === selectedIndex ? 'text-blue-400' : 'text-gray-500'}`} />
                                <span className={`text-sm font-medium ${index === selectedIndex ? 'text-blue-100' : 'text-gray-300'}`}>
                                    {cmd.label}
                                </span>
                                {index === selectedIndex && <ArrowRight className="ml-auto w-4 h-4 text-blue-500" />}
                            </button>
                        ))
                    )}
                </div>

                {/* Footer */}
                <div className="bg-gray-900/50 px-4 py-2 border-t border-gray-800 flex items-center justify-between text-xs text-gray-500">
                    <div className="flex gap-4">
                        <span><kbd className="font-sans bg-gray-800 rounded px-1">↵</kbd> to select</span>
                        <span><kbd className="font-sans bg-gray-800 rounded px-1">↑↓</kbd> to navigate</span>
                    </div>
                    <span>Nexi Sentinel</span>
                </div>
            </div>
        </div>,
        document.body
    );
}
