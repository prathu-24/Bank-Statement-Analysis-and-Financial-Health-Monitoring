import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  Calendar,
  Edit2,
  Check,
  X,
  ArrowDownLeft,
  ArrowUpRight,
  Sparkles,
  HelpCircle,
  Tag
} from 'lucide-react';
import { statementApi } from '../services/api';

const STANDARD_CATEGORIES = [
  "Income",
  "Food & Dining",
  "Transport",
  "Subscriptions",
  "Shopping",
  "Utilities & Bills",
  "Housing & Rent",
  "Loans & EMI",
  "Investments",
  "Healthcare",
  "Transfers",
  "Uncategorized"
];

export default function TransactionsPage() {
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [monthFilter, setMonthFilter] = useState('ALL');
  const [availableCategories, setAvailableCategories] = useState(STANDARD_CATEGORIES);

  // Edit category modal state
  const [editingTx, setEditingTx] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [applyToAll, setApplyToAll] = useState(false);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    fetchTransactions();
    fetchCategories();
  }, [categoryFilter, monthFilter]);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const data = await statementApi.getTransactions({
        category: categoryFilter,
        month: monthFilter,
        search: search || undefined,
        limit: 150
      });
      setTransactions(data.transactions || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error("Transactions fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const cats = await statementApi.getDashboardSummary('ALL');
      if (cats && cats.category_breakdown) {
        const unique = Array.from(new Set([...STANDARD_CATEGORIES, ...cats.category_breakdown.map(c => c.category)]));
        setAvailableCategories(unique);
      }
    } catch (err) {
      // fallback to standard
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchTransactions();
  };

  const openEditCategory = (tx) => {
    setEditingTx(tx);
    setSelectedCategory(tx.category || 'Uncategorized');
    setApplyToAll(false);
  };

  const handleSaveCategory = async () => {
    if (!editingTx || !selectedCategory) return;
    setUpdating(true);
    try {
      await statementApi.updateCategory(editingTx.id, selectedCategory, applyToAll);
      setEditingTx(null);
      fetchTransactions();
    } catch (err) {
      alert("Failed to update category: " + (err.message || "Unknown error"));
    } finally {
      setUpdating(false);
    }
  };

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2
    }).format(val || 0);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white">Transactions Audit Ledger</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Verified records normalized with deterministic categorization & merchant grouping
          </p>
        </div>
        <div className="text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl font-mono">
          Showing {transactions.length} of {total} records
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by merchant, narration, or reference..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-800/80 border border-slate-700/80 text-xs text-white rounded-xl pl-10 pr-4 py-2.5 focus:outline-none focus:border-indigo-500"
          />
        </form>

        <div className="flex items-center gap-2">
          {/* Category Filter */}
          <div className="flex items-center gap-1.5 bg-slate-800/80 border border-slate-700/80 rounded-xl px-2.5 py-1.5">
            <Tag className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-transparent text-xs text-white focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-slate-900">All Categories</option>
              {availableCategories.map((c) => (
                <option key={c} value={c} className="bg-slate-900">{c}</option>
              ))}
            </select>
          </div>

          <button
            onClick={fetchTransactions}
            className="px-3 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition"
          >
            Apply
          </button>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full text-xs text-left">
            <thead className="bg-slate-800/60 text-slate-400 uppercase font-semibold">
              <tr>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Description & Merchant</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3 text-right">Debit (-)</th>
                <th className="px-4 py-3 text-right">Credit (+)</th>
                <th className="px-4 py-3 text-right">Balance</th>
                <th className="px-4 py-3 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {transactions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                    {loading ? "Loading transactions..." : "No matching transactions found."}
                  </td>
                </tr>
              ) : (
                transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-800/30 transition">
                    <td className="px-4 py-3 text-slate-300 font-mono whitespace-nowrap">{tx.date}</td>
                    <td className="px-4 py-3">
                      <div className="text-white font-medium truncate max-w-xs">{tx.description}</div>
                      <div className="text-[10px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                        <span className="px-1.5 py-0.2 rounded bg-slate-800 text-indigo-300 font-mono">
                          {tx.normalized_merchant}
                        </span>
                        {tx.reference_id && (
                          <span className="text-slate-500 font-mono">Ref: {tx.reference_id}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => openEditCategory(tx)}
                        className={`group inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold transition ${
                          tx.user_overridden
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 hover:border-indigo-500/40'
                        }`}
                      >
                        {tx.category}
                        <Edit2 className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </button>
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-medium whitespace-nowrap text-rose-400">
                      {tx.debit > 0 ? `-${formatINR(tx.debit)}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-medium whitespace-nowrap text-emerald-400">
                      {tx.credit > 0 ? `+${formatINR(tx.credit)}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-semibold whitespace-nowrap text-white">
                      {formatINR(tx.balance)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => openEditCategory(tx)}
                        className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
                        title="Edit category"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Category Modal */}
      {editingTx && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Tag className="w-4 h-4 text-indigo-400" />
                Change Category
              </h3>
              <button
                onClick={() => setEditingTx(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div>
                <span className="text-[11px] text-slate-400 block">Transaction:</span>
                <span className="text-xs text-white font-medium block truncate mt-0.5">
                  {editingTx.description}
                </span>
                <span className="text-[10px] text-indigo-400 font-mono mt-0.5 block">
                  Detected Merchant: {editingTx.normalized_merchant}
                </span>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                  Select New Category
                </label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  {availableCategories.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              <div className="p-3 bg-slate-800/60 border border-slate-700/60 rounded-xl">
                <label className="flex items-start gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={applyToAll}
                    onChange={(e) => setApplyToAll(e.target.checked)}
                    className="rounded border-slate-700 text-indigo-600 focus:ring-0 mt-0.5"
                  />
                  <div className="text-[11px] text-slate-300 leading-tight">
                    <strong className="text-white block font-medium">Remember for this merchant</strong>
                    Apply "{selectedCategory}" to all current and future transactions from <strong>{editingTx.normalized_merchant}</strong>.
                  </div>
                </label>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 mt-6 pt-3 border-t border-slate-800">
              <button
                disabled={updating}
                onClick={() => setEditingTx(null)}
                className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 rounded-lg"
              >
                Cancel
              </button>
              <button
                disabled={updating}
                onClick={handleSaveCategory}
                className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg flex items-center gap-1.5 shadow-lg shadow-indigo-600/30"
              >
                <Check className="w-3.5 h-3.5" />
                {updating ? "Saving..." : "Save Category"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

