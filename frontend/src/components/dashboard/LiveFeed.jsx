import React from "react";
import { Maximize2, Siren, Zap } from "lucide-react";

const LiveFeed = () => {
  return (
    <div className="relative rounded-2xl overflow-hidden border border-white/10 group bg-black/50 aspect-video">
      <img
        src="http://127.0.0.1:5000/video_feed"
        alt="Live Feed"
        className="rounded-lg shadow-lg border border-gray-700"
      />

      {/* Overlay Header */}
      <div className="absolute top-4 left-4 right-4 flex justify-between items-start">
        <div className="flex gap-2">
          <span className="px-2 py-1 bg-red-600/80 text-white text-xs font-bold rounded animate-pulse">
            LIVE
          </span>
          <span className="px-2 py-1 bg-black/60 backdrop-blur text-white text-xs rounded border border-white/10">
            Camera 01 - Main Street
          </span>
        </div>

        <div className="flex gap-2">
          <div className="flex items-center gap-1 px-2 py-1 bg-black/60 rounded-full border border-white/10 text-xs text-gray-300">
            <div className="w-2 h-2 rounded-full bg-neon-red animate-pulse" />
            Siren Sound
          </div>
          <div className="flex items-center gap-1 px-2 py-1 bg-black/60 rounded-full border border-white/10 text-xs text-gray-300">
            <div className="w-2 h-2 rounded-full bg-neon-blue animate-pulse delay-75" />
            Flashing Light
          </div>
        </div>
      </div>

      <button className="absolute bottom-4 right-4 p-2 bg-black/50 hover:bg-neon-blue/20 text-white rounded-lg transition-colors border border-white/10">
        <Maximize2 size={18} />
      </button>
    </div>
  );
};

export default LiveFeed;
