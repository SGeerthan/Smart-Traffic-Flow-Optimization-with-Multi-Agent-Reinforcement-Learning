import React from 'react';
import { LayoutGrid, Camera, BarChart2, Bell, Map as MapIcon, Settings } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import clsx from 'clsx';

const SidebarItem = ({ to, icon: Icon, label }) => (
    <NavLink
        to={to}
        className={({ isActive }) =>
            clsx(
                "p-3 rounded-xl transition-all duration-300 group relative flex items-center justify-center",
                isActive
                    ? "bg-neon-blue/10 text-neon-blue shadow-[0_0_10px_rgba(0,243,255,0.3)]"
                    : "text-gray-500 hover:text-gray-300 hover:bg-white/5"
            )
        }
    >
        <Icon size={24} />
        {/* Tooltip */}
        <span className="absolute left-14 bg-dark-surface border border-white/10 px-2 py-1 rounded text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
            {label}
        </span>
        {/* Active Line Indicator */}
        <div className={clsx(
            "absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full bg-neon-blue transition-all duration-300",
            // isActive ? "opacity-100" : "opacity-0" // Using conditional rendering for cleaner DOM or just class
        )}
            style={{ opacity: 0 }} // Simplified for now, relying on background
        />
    </NavLink>
);

const Sidebar = () => {
    return (
        <aside className="fixed left-0 top-0 h-screen w-20 bg-dark-base border-r border-white/5 flex flex-col items-center py-6 z-40">
            <div className="mb-10 p-2">
                <div className="w-8 h-8 rounded bg-gradient-to-tr from-neon-blue to-neon-purple shadow-[0_0_15px_rgba(0,243,255,0.5)]" />
            </div>

            <nav className="flex flex-col gap-6 w-full px-2">
                <SidebarItem to="/" icon={LayoutGrid} label="Dashboard" />
                <SidebarItem to="/live" icon={Camera} label="Live Feed" />
                <SidebarItem to="/analytics" icon={BarChart2} label="Analytics" />
                <SidebarItem to="/alerts" icon={Bell} label="Alerts" />
                <SidebarItem to="/map" icon={MapIcon} label="Map View" />
            </nav>

            <div className="mt-auto mb-4">
                <SidebarItem to="/settings" icon={Settings} label="Settings" />
            </div>
        </aside>
    );
};

export default Sidebar;
