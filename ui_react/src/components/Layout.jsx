import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    MessageSquare,
    FileText,
    Database,
    Settings,
    Activity,
    Share2
} from 'lucide-react';

const Layout = ({ children }) => {
    const location = useLocation();

    const navItems = [
        { path: '/', label: 'Dashboard', icon: LayoutDashboard },
        { path: '/playground', label: 'Playground', icon: MessageSquare },
        { path: '/evaluation', label: 'Evaluation Studio', icon: Activity },
        { path: '/graph', label: 'Graph Explorer', icon: Share2 },
        { path: '/data', label: 'Data Manager', icon: Database },
        { path: '/settings', label: 'Settings', icon: Settings },
    ];

    return (
        <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
            {/* Sidebar */}
            <aside className="w-64 bg-white border-r border-slate-200 flex flex-col">
                <div className="p-6 border-b border-slate-100">
                    <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                        Hybrid RAG
                    </h1>
                    <p className="text-xs text-slate-500 mt-1">Evaluation Expert</p>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${isActive
                                    ? 'bg-blue-50 text-blue-700'
                                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                                    }`}
                            >
                                <Icon size={18} />
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-slate-100">
                    <div className="flex items-center gap-3 px-3 py-2">
                        <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-xs">
                            EX
                        </div>
                        <div className="text-sm">
                            <p className="font-medium text-slate-900">Expert Mode</p>
                            <p className="text-xs text-slate-500">Active</p>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
                <div className="max-w-7xl mx-auto p-8">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default Layout;
