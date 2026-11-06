import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  LayoutDashboard,
  Receipt,
  Repeat,
  TrendingUp,
  Sparkles,
  Shield,
  Trash2,
  Menu,
  X,
  CreditCard
} from 'lucide-react';
import { statementApi } from '../services/api';

export default function DashboardLayout() {
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const navItems = [
    { label: 'Upload Statement', path: '/upload', icon: UploadCloud },
    { label: 'Financial Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Transactions', path: '/transactions', icon: Receipt },
    { label: 'Recurring Payments', path: '/recurring', icon: Repeat },
    { label: 'Cash-Flow Forecast', path: '/forecast', icon: TrendingUp },
    { label: 'AI Financial Insights', path: '/insights', icon: Sparkles },
  ];

  const handleDeleteAll = async () => {
    setDeleting(true);
    try {
      await statementApi.deleteAllData();
      setDeleteModalOpen(false);
      navigate('/upload');
    } catch (err) {
      alert("Failed to delete user data: " + (err.message || "Unknown error"));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#080d1a] text-slate-100 overflow-hidden">
      {/* Sidebar Desktop */}
      <aside className="hidden md:flex flex-col w-64 bg-[#0d1527] border-r border-slate-800/80 p-4 justify-between">
        <div className="space-y-6">
          {/* Logo */}
          <div className="flex items-center gap-3 px-2 py-1">
            <div className="p-2 bg-gradient-to-tr from-indigo-600 to-indigo-400 rounded-xl shadow-lg shadow-indigo-500/20">
              <CreditCard className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                FinSight <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">AI</span>
              </span>
              <p className="text-[11px] text-slate-400">Statement Intelligence</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                      isActive
                        ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Privacy Panel & Purge Action */}
        <div className="space-y-3 pt-4 border-t border-slate-800/80">
          <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl">
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold">
              <Shield className="w-3.5 h-3.5" />
              Privacy Shield Active
            </div>
            <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
              No statements are stored permanently. Analytics operate locally in-memory.
            </p>
          </div>

          <button
            onClick={() => setDeleteModalOpen(true)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-semibold text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-xl border border-rose-500/20 transition"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Delete All My Data
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Header */}
        <header className="md:hidden flex items-center justify-between p-4 bg-[#0d1527] border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-indigo-600 rounded-lg">
              <CreditCard className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-white">FinSight</span>
          </div>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-slate-400 hover:text-white"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </header>

        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-[#0d1527] border-b border-slate-800 p-4 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold ${
                      isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </NavLink>
              );
            })}
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                setDeleteModalOpen(true);
              }}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-rose-400"
            >
              <Trash2 className="w-4 h-4" />
              Delete All My Data
            </button>
          </div>
        )}

        {/* Page Content Body */}
        <main className="flex-1 overflow-y-auto bg-[#080d1a] p-4 md:p-8">
          <Outlet />
        </main>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center gap-3 text-rose-400 mb-3">
              <div className="p-2 bg-rose-500/10 rounded-xl">
                <Trash2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Delete All Stored Data?</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              This action will permanently delete all uploaded transactions, category overrides, 
              recurring payment models, and alert dismissals from the database. 
              This operation cannot be undone.
            </p>
            <div className="flex items-center justify-end gap-3 mt-6">
              <button
                disabled={deleting}
                onClick={() => setDeleteModalOpen(false)}
                className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 rounded-lg"
              >
                Cancel
              </button>
              <button
                disabled={deleting}
                onClick={handleDeleteAll}
                className="px-4 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-500 rounded-lg flex items-center gap-2"
              >
                {deleting ? "Purging..." : "Yes, Purge Everything"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

