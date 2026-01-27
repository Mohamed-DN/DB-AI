import React, { useState } from 'react';
import { X, ShieldCheck, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

interface AddInstanceModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export default function AddInstanceModal({ isOpen, onClose, onSuccess }: AddInstanceModalProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [formData, setFormData] = useState({
        name: '',
        url: '',
        username: '',
        password: '',
        verify_ssl: false
    });

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/oem/instances', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to add instance');
            }

            onSuccess();
            onClose();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in">
            <div className="w-full max-w-md bg-[#1e293b] border border-gray-700 rounded-xl shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-700 bg-gray-800/50">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-purple-500/20">
                            <ShieldCheck className="w-5 h-5 text-purple-400" />
                        </div>
                        <h2 className="text-xl font-semibold text-white">Add OEM Instance</h2>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Body */}
                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    {error && (
                        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
                            <AlertCircle className="w-4 h-4" />
                            {error}
                        </div>
                    )}

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">Instance Name</label>
                            <input
                                type="text"
                                required
                                placeholder="e.g. OEM Production"
                                className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                                value={formData.name}
                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">OEM URL</label>
                            <input
                                type="url"
                                required
                                placeholder="https://oem.example.com:7803/em"
                                className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                                value={formData.url}
                                onChange={e => setFormData({ ...formData, url: e.target.value })}
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Username</label>
                                <input
                                    type="text"
                                    required
                                    placeholder="sysman"
                                    className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                                    value={formData.username}
                                    onChange={e => setFormData({ ...formData, username: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Password</label>
                                <input
                                    type="password"
                                    required
                                    className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                                    value={formData.password}
                                    onChange={e => setFormData({ ...formData, password: e.target.value })}
                                />
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            <input
                                type="checkbox"
                                id="verify_ssl"
                                className="rounded border-gray-700 bg-gray-950 text-purple-500 focus:ring-purple-500/50"
                                checked={formData.verify_ssl}
                                onChange={e => setFormData({ ...formData, verify_ssl: e.target.checked })}
                            />
                            <label htmlFor="verify_ssl" className="text-sm text-gray-400 select-none">Verify SSL Certificate</label>
                        </div>
                    </div>

                    <div className="pt-4 flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 rounded-lg bg-gray-800 text-gray-300 hover:text-white hover:bg-gray-700 transition-colors text-sm font-medium"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="px-6 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white transition-colors text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Connecting...
                                </>
                            ) : (
                                <>
                                    <CheckCircle className="w-4 h-4" />
                                    Connect & Save
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
