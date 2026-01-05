import React from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import { Outlet } from 'react-router-dom';

const DashboardLayout = () => {
    return (
        <div className="min-h-screen bg-dark-base flex">
            <Sidebar />
            <div className="flex-1 ml-20 flex flex-col">
                <Header />
                <main className="flex-1 p-6 overflow-y-auto overflow-x-hidden">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default DashboardLayout;
