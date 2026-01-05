import React from 'react';
import StatCard from '../components/dashboard/StatCard';
import LiveFeed from '../components/dashboard/LiveFeed';
import AudioWidget from '../components/dashboard/AudioWidget';
import { Activity } from 'lucide-react';

const DashboardHome = () => {
    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">

            {/* Top Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
               
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[500px]">
                {/* Live Feed - Takes 2/3 width */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-medium text-white flex items-center gap-2">
                            <Activity className="text-neon-blue" />
                            Real-Time Detection Feed
                        </h2>
                        <div className="flex gap-3 text-sm text-gray-400">
                            <span className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-gray-600" /> Siren Sound
                            </span>
                            <span className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-gray-600" /> Flashing Light
                            </span>
                        </div>
                    </div>

                    <div className="h-[calc(100%-2rem)]">
                        <LiveFeed />
                    </div>
                </div>

                {/* Right Column: Audio & Activity */}
                <div className="space-y-6 h-full flex flex-col">
                    <div className="flex-1">
                        <AudioWidget />
                    </div>

                    {/* Flashing Light Widget Placeholder */}
                    <div className="h-32 p-4 rounded-xl bg-dark-surface border border-white/10 flex items-center justify-between relative overflow-hidden">
                        <div className="z-10">
                            <div className="text-gray-400 text-sm mb-1">Light Detection</div>
                            <div className="text-xl font-bold text-white">Detecting...</div>
                        </div>
                        <div className="w-12 h-12 rounded-full bg-gray-800 border border-gray-700 animate-pulse z-10" />

                        {/* Animated Background Strobe Effect (Subtle) */}
                        <div className="absolute inset-0 bg-neon-blue/5 animate-pulse" />
                    </div>
                </div>
            </div>

        </div>
    );
};

export default DashboardHome;
