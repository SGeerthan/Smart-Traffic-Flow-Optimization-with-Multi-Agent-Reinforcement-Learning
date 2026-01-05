import React from 'react';
import { Bell, User, Settings, Search } from 'lucide-react';

const Header = () => {
    return (
        <header className="h-16 flex items-center justify-between px-8 border-b border-white/5 bg-dark-base/50 backdrop-blur-sm sticky top-0 z-30">
            <div>
                <h1 className="text-xl font-medium tracking-wide text-neon-blue drop-shadow-[0_0_5px_rgba(0,243,255,0.5)]">
                    Emergency Detection & Monitoring Dashboard
                </h1>
            </div>

            <div className="flex items-center gap-6">
                {/* Search Placeholder */}
                <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 focus-within:border-neon-blue/50 transition-colors">
                    <Search size={16} className="text-gray-500" />
                    <input
                        type="text"
                        placeholder="Search logs..."
                        className="bg-transparent border-none outline-none text-sm text-gray-200 placeholder-gray-600 w-48"
                    />
                </div>

                <div className="flex items-center gap-4 text-gray-400">
                    <button className="hover:text-neon-blue transition-colors relative">
                        <Bell size={20} />
                        <span className="absolute -top-1 -right-1 w-2 h-2 bg-neon-red rounded-full animate-pulse" />
                    </button>

                    <button className="hover:text-neon-blue transition-colors">
                        <User size={20} />
                    </button>

                    <button className="hover:text-neon-blue transition-colors">
                        <Settings size={20} />
                    </button>
                </div>
            </div>
        </header>
    );
};

export default Header;
