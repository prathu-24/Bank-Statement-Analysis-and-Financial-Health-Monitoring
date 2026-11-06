import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Wallet,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  Layers,
  ShoppingBag,
  HelpCircle,
  UploadCloud,
  ChevronRight
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  CartesianGrid
} from 'recharts';
import { statementApi } from '../services/api';
import EvidenceDrawer from '../components/EvidenceDrawer';
import DebtSpiralRadar from '../components/health/DebtSpiralRadar';

const CATEGORY_COLORS = [
  '#6366f1', '#ec4899', '#10b981', '#f59e0b',
  '#3b82f6', '#8b5cf6', '#14b8a6', '#f43f5e',
  '#a855f7', '#06b6d4', '#84cc16', '#64748b'
];

export default function DashboardPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [selectedMonth, setSelectedMonth] = useState('ALL');
  const [whyModal, setWhyModal] = useState({ open: false, title: '', content: '' });
  const [evidenceDrawer, setEvidenceDrawer] = useState({ open: false, title: '', queryParams: null });

  useEffect(() => {
    fetchSummary(selectedMonth);
  }, [selectedMonth]);

  const fetchSummary = async (month) => {
    setLoading(true);
    try {
      const summary = await statementApi.getDashboardSummary(month);
      setData(summary);
      if (month === 'ALL' && summary.selected_month) {
        // keep current
      }
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val || 0);
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading Financial Intelligence Dashboard...</p>
        </div>
      </div>
    );
  }

  if (!data || !data.has_data) {
    return (
      <div className="max-w-md mx-auto text-center py-16 space-y-4">
        <div className="w-16 h-16 bg-indigo-500/10 text-indigo-400 rounded-2xl flex items-center justify-center mx-auto border border-indigo-500/20">
          <Wallet className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-white">No Statement Data Yet</h2>
        <p className="text-xs text-slate-400 leading-relaxed">
          Upload an HDFC, SBI, Generic CSV or Bank Statement PDF to view comprehensive cash-flow intelligence and metrics.
        </p>
        <button
          onClick={() => navigate('/upload')}
          className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl flex items-center gap-2 mx-auto shadow-lg shadow-indigo-600/30 transition"
        >
          <UploadCloud className="w-4 h-4" />
          Upload Statement
        </button>
      </div>
    );
  }

  const { kpi, mom, monthly_trends, category_breakdown, top_merchants, available_months } = data;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Bar with Title and Month Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white">Financial Dashboard</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time cash flow, category breakdowns, and month-over-month trajectory
          </p>
        </div>

        {/* Month Selector */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1 rounded-xl">
          <Calendar className="w-4 h-4 text-slate-400 ml-2" />
          <select
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="bg-transparent text-xs font-semibold text-white px-2 py-1.5 focus:outline-none cursor-pointer"
          >
            <option value="ALL" className="bg-slate-900 text-white">All Recorded History</option>
            {available_months.map((m) => (
              <option key={m} value={m} className="bg-slate-900 text-white">
                {m}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Income Card */}
        <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Income</span>
            <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-xl">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-bold text-white">{formatINR(kpi.total_income)}</span>
            <button
              onClick={() => setEvidenceDrawer({
                open: true,
                title: `Total Income Proof Trail (${selectedMonth})`,
                queryParams: { metric: 'total_income', month: selectedMonth }
              })}
              className="text-[11px] font-semibold text-emerald-400 hover:text-emerald-300 hover:underline"
            >
              Audit Proof &rarr;
            </button>
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px]">
            {mom.income_change_pct !== 0 ? (
              <span className={`flex items-center gap-0.5 font-semibold ${
                mom.income_change_pct > 0 ? 'text-emerald-400' : 'text-rose-400'
              }`}>
                {mom.income_change_pct > 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                {Math.abs(mom.income_change_pct)}% MoM
              </span>
            ) : (
              <span className="text-slate-400">Stable inflow</span>
            )}
            <button
              onClick={() => setWhyModal({
                open: true,
                title: 'Total Income Calculation',
                content: `Total credited transactions across the period: ${formatINR(kpi.total_income)}. Calculated by summing all credit column entries.`
              })}
              className="text-slate-400 hover:text-white"
            >
              <HelpCircle className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Expense Card */}
        <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Expenses</span>
            <div className="p-2 bg-rose-500/10 text-rose-400 rounded-xl">
              <TrendingDown className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-2xl font-bold text-white">{formatINR(kpi.total_expense)}</span>
            <button
              onClick={() => setEvidenceDrawer({
                open: true,
                title: `Total Expense Proof Trail (${selectedMonth})`,
                queryParams: { metric: 'total_spend', month: selectedMonth }
              })}
              className="text-[11px] font-semibold text-rose-400 hover:text-rose-300 hover:underline"
            >
              Audit Proof &rarr;
            </button>
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px]">
            {mom.expense_change_pct !== 0 ? (
              <span className={`flex items-center gap-0.5 font-semibold ${
                mom.expense_change_pct > 0 ? 'text-rose-400' : 'text-emerald-400'
              }`}>
                {mom.expense_change_pct > 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                {Math.abs(mom.expense_change_pct)}% MoM
              </span>
            ) : (
              <span className="text-slate-400">Historical average</span>
            )}
            <button
              onClick={() => setWhyModal({
                open: true,
                title: 'Total Expense Calculation',
                content: `Total debited transactions across the period: ${formatINR(kpi.total_expense)}. Calculated by summing all debit column records.`
              })}
              className="text-slate-400 hover:text-white"
            >
              <HelpCircle className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Net Savings Card */}
        <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Net Savings</span>
            <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl">
              <Wallet className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className={`text-2xl font-bold ${kpi.net_savings >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {formatINR(kpi.net_savings)}
            </span>
            <button
              onClick={() => setEvidenceDrawer({
                open: true,
                title: `Net Savings Inflow/Outflow Rows (${selectedMonth})`,
                queryParams: { metric: 'net_savings', month: selectedMonth }
              })}
              className="text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 hover:underline"
            >
              Audit Proof &rarr;
            </button>
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px]">
            <span className="text-slate-300 font-semibold">
              Savings Rate: <strong className="text-indigo-400">{kpi.savings_rate}%</strong>
            </span>
            <button
              onClick={() => setWhyModal({
                open: true,
                title: 'Savings Rate Metric',
                content: `Formula: (Net Savings / Total Income) * 100. (${formatINR(kpi.net_savings)} / ${formatINR(kpi.total_income)}) * 100 = ${kpi.savings_rate}%. A rate > 20% indicates healthy financial retention.`
              })}
              className="text-slate-400 hover:text-white"
            >
              <HelpCircle className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Current Available Balance */}
        <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Latest Verified Balance</span>
            <div className="p-2 bg-blue-500/10 text-blue-400 rounded-xl">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-white">{formatINR(kpi.current_balance)}</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px]">
            <span className="text-slate-400">{kpi.transaction_count} transactions verified</span>
            <button
              onClick={() => setWhyModal({
                open: true,
                title: 'Latest Verified Balance',
                content: `Closing balance extracted from the latest chronologically verified transaction in the bank ledger: ${formatINR(kpi.current_balance)}.`
              })}
              className="text-slate-400 hover:text-white"
            >
              <HelpCircle className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Charts Grid: Monthly Inflow vs Outflow & Category Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Income vs Expenses Bar Chart */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-sm font-semibold text-white">Monthly Cash Flow Comparison</h3>
              <p className="text-xs text-slate-400 mt-0.5">Inflow (Credits) vs Outflow (Debits)</p>
            </div>
            <button
              onClick={() => setWhyModal({
                open: true,
                title: 'Cash Flow Comparison Chart',
                content: 'Aggregates monthly credits and debits to highlight net cash accumulation or burn rate across successive statement periods.'
              })}
              className="text-slate-400 hover:text-white"
            >
              <HelpCircle className="w-4 h-4" />
            </button>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthly_trends} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="month" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={(v) => `₹${v/1000}k`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                  formatter={(val) => formatINR(val)}
                />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                <Bar dataKey="income" name="Income" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="expenses" name="Expenses" fill="#f43f5e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Breakdown Donut Chart */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-white">Category Distribution</h3>
                <p className="text-xs text-slate-400 mt-0.5">Share of total outlays</p>
              </div>
              <button
                onClick={() => setWhyModal({
                  open: true,
                  title: 'Expense Categorization Breakdown',
                  content: 'Categorized using deterministic keyword matching (e.g. Swiggy -> Food, Uber -> Transport) combined with user-confirmed overrides.'
                })}
                className="text-slate-400 hover:text-white"
              >
                <HelpCircle className="w-4 h-4" />
              </button>
            </div>

            <div className="h-48 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={category_breakdown}
                    dataKey="amount"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={3}
                  >
                    {category_breakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                    formatter={(val) => formatINR(val)}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Category List */}
          <div className="mt-4 space-y-2 max-h-36 overflow-y-auto pr-1">
            {category_breakdown.slice(0, 5).map((cat, idx) => (
              <div
                key={cat.category}
                onClick={() => setEvidenceDrawer({
                  open: true,
                  title: `${cat.category} Evidence Rows (${selectedMonth})`,
                  queryParams: { metric: 'category_spend', category: cat.category, month: selectedMonth }
                })}
                className="flex items-center justify-between text-xs p-1 rounded-lg hover:bg-slate-800/60 cursor-pointer transition"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length] }}
                  />
                  <span className="text-slate-300 truncate max-w-[120px]">{cat.category}</span>
                </div>
                <div className="flex items-center gap-2 font-mono">
                  <span className="text-white">{formatINR(cat.amount)}</span>
                  <span className="text-[10px] text-slate-400">({cat.percentage}%)</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Debt-Spiral Risk Radar Panel */}
      <DebtSpiralRadar />

      {/* Bottom Grid: Top Merchants and MoM Savings Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Merchants Leaderboard */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Top Spending Outlets</h3>
              <p className="text-xs text-slate-400 mt-0.5">Ranked by total debit volume</p>
            </div>
            <button
              onClick={() => navigate('/transactions')}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
            >
              View All <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {top_merchants.map((m, idx) => {
              const maxSpend = top_merchants[0]?.amount || 1;
              const barWidth = Math.min(100, Math.round((m.amount / maxSpend) * 100));
              return (
                <div
                  key={m.merchant}
                  onClick={() => setEvidenceDrawer({
                    open: true,
                    title: `${m.merchant} Statement Transactions`,
                    queryParams: { metric: 'recurring_item', merchant: m.merchant, month: selectedMonth }
                  })}
                  className="space-y-1 p-1 rounded-lg hover:bg-slate-800/50 cursor-pointer transition"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-200 flex items-center gap-2">
                      <span className="text-[10px] text-slate-500 font-mono w-4">#{idx + 1}</span>
                      {m.merchant}
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                        {m.category}
                      </span>
                    </span>
                    <span className="font-semibold text-white font-mono">{formatINR(m.amount)}</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 rounded-full"
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Savings Trend Line Chart */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Savings Rate Trajectory</h3>
              <p className="text-xs text-slate-400 mt-0.5">% of income retained each month</p>
            </div>
            <button
              onClick={() => setWhyModal({
                open: true,
                title: 'Savings Trajectory Analysis',
                content: 'Tracks whether your monthly retention is expanding or compressing over time. A sustained dip below 10% triggers early financial distress warnings.'
              })}
              className="text-slate-400 hover:text-white"
            >
              <HelpCircle className="w-4 h-4" />
            </button>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={monthly_trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="month" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                  formatter={(val) => `${val}%`}
                />
                <Line
                  type="monotone"
                  dataKey="savings_rate"
                  name="Savings Rate (%)"
                  stroke="#6366f1"
                  strokeWidth={3}
                  dot={{ r: 4, fill: '#818cf8' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* "Why am I seeing this?" Modal */}
      {whyModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center gap-3 text-indigo-400 mb-3">
              <div className="p-2 bg-indigo-500/10 rounded-xl">
                <HelpCircle className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">{whyModal.title}</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">{whyModal.content}</p>
            <div className="flex justify-end mt-5">
              <button
                onClick={() => setWhyModal({ open: false, title: '', content: '' })}
                className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg transition"
              >
                Understood
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Evidence Proof Drawer */}
      <EvidenceDrawer
        isOpen={evidenceDrawer.open}
        onClose={() => setEvidenceDrawer({ open: false, title: '', queryParams: null })}
        title={evidenceDrawer.title}
        queryParams={evidenceDrawer.queryParams}
      />
    </div>
  );
}

