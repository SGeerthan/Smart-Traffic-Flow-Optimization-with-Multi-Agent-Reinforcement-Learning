import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './components/layouts/DashboardLayout';
import DashboardHome from './pages/DashBoardHome';
// import Analytics from './pages/Analytics';
// import MapView from './pages/MapView';
// import AlertsLogs from './pages/AlertsLogs';
// import Settings from './pages/Settings';

// Placeholder Pages
const LiveFeedPage = () => <div className="text-white p-10 flex items-center justify-center h-full text-2xl font-mono text-neon-blue animate-pulse">Live Feed - Full Screen Mode Active</div>;

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<DashboardHome />} />
          {/* <Route path="live" element={<LiveFeedPage />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="alerts" element={<AlertsLogs />} />
          <Route path="map" element={<MapView />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} /> */}
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
