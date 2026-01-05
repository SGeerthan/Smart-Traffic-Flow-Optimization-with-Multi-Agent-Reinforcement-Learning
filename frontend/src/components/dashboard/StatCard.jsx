import React from 'react';
import { Ambulance, Flame, Shield, Crown } from 'lucide-react';
import clsx from 'clsx';

const iconMap = {
    ambulance: Ambulance,
    flame: Flame,
    shield: Shield,
    crown: Crown
};

const StatCard = ({ type, count, color, borderColor, icon }) => {
    const Icon = iconMap[icon] || Shield;

    return (
        <div className={clsx(
            "relative p-6 rounded-2xl bg-dark-surface border backdrop-blur-sm overflow-hidden group transition-all duration-300 hover:scale-[1.02]",
            borderColor ? borderColor : "border-white/10" // Handle custom neon border classes
        )}>
            {/* Background Glow */}
            <div className={clsx("absolute -right-10 -top-10 w-32 h-32 rounded-full opacity-10 blur-3xl", color.replace('text-', 'bg-'))} />

            <div className="flex justify-between items-start mb-4">
                <Icon className={clsx("w-8 h-8", color)} />
                <span className="text-xs text-gray-400 font-medium uppercase tracking-wider">Today</span>
            </div>

            <div className="flex flex-col">
                <span className={clsx("text-4xl font-bold tracking-tight mb-1", color)}>
                    {count}
                </span>
                <span className="text-gray-400 text-sm font-medium">{type}</span>
            </div>
        </div>
    );
};

export default StatCard;
