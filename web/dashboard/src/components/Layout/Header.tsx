import {
    Search,
    User,
    LogOut,
    ExternalLink,
    Pause,
    Play,
    Share2
} from 'lucide-react';
import { useState } from 'react';

interface HeaderProps {
    pageTitle: string;
    user: any;
    logout: () => void;
    isPaused: boolean;
    togglePause: () => void;
    onSearchClick: () => void;
}

export default function Header({
    pageTitle,
    user,
    logout,
    isPaused,
    togglePause,
    onSearchClick
}: HeaderProps) {
    const [showUserMenu, setShowUserMenu] = useState(false);

    return (
        <header className="h-16 sticky top-0 z-30 flex items-center justify-between px-6 glass bg-gray-900/80 border-b border-gray-800 backdrop-blur-md">
            {/* Left: Breadcrumbs / Title */}
            <div className="flex items-center gap-4">
                <div className="flex flex-col">
                    <span className="text-xs text-gray-500 font-mono uppercase tracking-widest">Nexi / Sentinel</span>
                    <h2 className="text-lg font-semibold text-gray-100">{pageTitle}</h2>
                </div>
            </div>

            {/* Center: Search Bar (Fake Input Trigger) */}
            <div className="flex-1 max-w-xl mx-8">
                <button
                    onClick={onSearchClick}
                    className="w-full flex items-center gap-3 px-4 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-gray-400 hover:bg-gray-800 hover:border-gray-600 transition-all group"
                >
                    <Search className="w-4 h-4 group-hover:text-white transition-colors" />
                    <span className="text-sm">Type anything to search...</span>
                    <span className="ml-auto text-xs bg-gray-700 px-2 py-0.5 rounded text-gray-300 group-hover:bg-gray-600">⌘K</span>
                </button>
            </div>

            {/* Right: Actions */}
            <div className="flex items-center gap-3">
                {/* Pause/Resume System */}
                <button
                    onClick={togglePause}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all
            ${isPaused
                            ? 'bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 border border-amber-500/20'
                            : 'bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 border border-emerald-500/20'
                        }`}
                >
                    {isPaused ? <Play size={14} /> : <Pause size={14} />}
                    {isPaused ? 'Resume System' : 'System Active'}
                </button>

                <div className="h-6 w-px bg-gray-800 mx-1"></div>

                {/* External Links */}
                <button
                    className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800"
                    title="Open MongoDB Express"
                    onClick={() => window.open(`http://localhost:${import.meta.env.VITE_MONGO_EXPRESS_PORT || '9081'}`, '_blank')}
                >
                    <ExternalLink size={18} />
                </button>

                {/* User Profile */}
                <div className="relative">
                    <button
                        onClick={() => setShowUserMenu(!showUserMenu)}
                        className="flex items-center gap-3 pl-3 py-1.5 rounded-lg hover:bg-gray-800 transition-colors"
                    >
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-500 to-pink-500 flex items-center justify-center text-xs font-bold text-white shadow-inner">
                            {user?.username?.substring(0, 2).toUpperCase() || 'US'}
                        </div>
                    </button>

                    {/* Dropdown */}
                    {showUserMenu && (
                        <div className="absolute right-0 mt-2 w-56 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl py-2 z-50 animate-in fade-in zoom-in-95 duration-200">
                            <div className="px-4 py-3 border-b border-gray-800">
                                <p className="text-sm font-medium text-white">{user?.full_name || 'Admin User'}</p>
                                <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                            </div>
                            <div className="py-1">
                                <button className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">
                                    <User size={14} /> Profile
                                </button>
                                <button className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800">
                                    <Share2 size={14} /> Share View
                                </button>
                            </div>
                            <div className="border-t border-gray-800 pt-1">
                                <button
                                    onClick={logout}
                                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-red-500/10"
                                >
                                    <LogOut size={14} /> Sign Out
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}
