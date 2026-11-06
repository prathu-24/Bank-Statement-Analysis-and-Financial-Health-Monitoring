import React, { useState, useEffect } from 'react';
import {
  Repeat,
  AlertTriangle,
  Calendar,
  CheckCircle,
  HelpCircle,
  Sparkles,
  ShieldAlert,
  ArrowRight,
  TrendingDown,
  Layers,
  Check,
  EyeOff,
  FileText
} from 'lucide-react';
import { statementApi } from '../services/api';
import EvidenceDrawer from '../components/EvidenceDrawer';

export default function RecurringPage() {
  const [loading, setLoading] = useState(true);
  const [recurringData, setRecurringData] = useState(null);
  const [anomaliesData, setAnomaliesData] = useState(null);
  const [tab, setTab] = useState('ALL');
  const [anomalyFilter, setAnomalyFilter] = useState('PENDING'); // PENDING or ALL
  const [whyModal, setWhyModal] = useState({ open: false, title: '', content: '' });
  const [evidenceDrawer, setEvidenceDrawer] = useState({ open: false, title: '', queryParams: null });
  const [dismissingId, setDismissingId] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [rec, ano] = await Promise.all([
        statementApi.getRecurringPayments(),
        statementApi.getAnomalies()
      ]);
      setRecurringData(rec);
      setAnomaliesData(ano);
    } catch (err) {
      console.error("Failed to load recurring / anomalies:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDismissAnomaly = async (alertId) => {
    setDismissingId(alertId);
    try {
      await statementApi.dismissAnomaly(alertId);
      // Optimistically update
      setAnomaliesData(prev => {
        if (!prev) return prev;
        const updatedAlerts = prev.alerts.map(a =>
          a.alert_id === alertId ? { ...a, is_dismissed: true } : a
        );
        return {
          ...prev,
          pending_count: Math.max(0, prev.pending_count - 1),
          dismissed_count: prev.dismissed_count + 1,
          alerts: updatedAlerts
        };
      });
    } catch (err) {
      alert("Failed to dismiss alert: " + (err.message || "Unknown error"));
    } finally {
      setDismissingId(null);
    }
  };

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val || 0);
  };

  if (loading && !recurringData) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Analyzing recurring commitments & cadence patterns...</p>
        </div>
      </div>
    );
  }

  const { summary = {}, commitments = [] } = recurringData || {};
  const { alerts = [], pending_count = 0 } = anomaliesData || {};

  const filteredCommitments = commitments.filter(item => {
    if (tab === 'ALL') return true;
    if (tab === 'SUBSCRIPTION') return item.classification === 'Subscription';
    if (tab === 'EMI') return item.classification === 'EMI / Loan' || item.classification === 'Housing / Rent';
    if (tab === 'FORGOTTEN') return item.is_potentially_forgotten;
    return true;
  });

  const displayedAlerts = alerts.filter(a => {
    if (anomalyFilter === 'PENDING') return !a.is_dismissed;
    return true;
  });

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white">Recurring Payments & Review Alerts</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Cadence detection, subscription audit, and statistical outlier review
          </p>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <span className="text-xs font-medium text-slate-400 block">Monthly Recurring Outlay</span>
          <span className="text-2xl font-bold text-white mt-1 block">
            {formatINR(summary.total_monthly_commitment)}
          </span>
          <span className="text-[11px] text-slate-400 mt-1 block">
            Normalized across {summary.total_commitments_count} repeating obligations
          </span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <span className="text-xs font-medium text-slate-400 block">Estimated Annual Commitment</span>
          <span className="text-2xl font-bold text-indigo-400 mt-1 block">
            {formatINR(summary.total_annual_commitment)}
          </span>
          <span className="text-[11px] text-slate-400 mt-1 block">
            Projected 12-month recurring expenditure
          </span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <span className="text-xs font-medium text-slate-400 block">Active Subscriptions</span>
          <span className="text-2xl font-bold text-emerald-400 mt-1 block">
            {summary.subscriptions_count}
          </span>
          <span className="text-[11px] text-slate-400 mt-1 block">
            Entertainment, apps & digital services
          </span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Potentially Forgotten</span>
            {summary.potential_forgotten_count > 0 && (
              <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                Action Recommended
              </span>
            )}
          </div>
          <span className="text-2xl font-bold text-amber-400 mt-1 block">
            {summary.potential_forgotten_count}
          </span>
          <span className="text-[11px] text-slate-300 font-semibold mt-1 block">
            Potential Savings: {formatINR(summary.potential_annual_savings)}/yr
          </span>
        </div>
      </div>

      {/* SECTION 1: Unusual Transactions - Please Review */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-amber-500/10 text-amber-400 rounded-xl">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white">Unusual - Please Review</h2>
                {pending_count > 0 && (
                  <span className="px-2 py-0.5 text-[11px] font-bold rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">
                    {pending_count} pending review
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Explainable anomalies detected using IQR, category Z-scores, and duplicate clustering.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-800/80 p-1 rounded-xl text-xs">
            <button
              onClick={() => setAnomalyFilter('PENDING')}
              className={`px-3 py-1 rounded-lg font-medium transition ${
                anomalyFilter === 'PENDING' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Pending ({pending_count})
            </button>
            <button
              onClick={() => setAnomalyFilter('ALL')}
              className={`px-3 py-1 rounded-lg font-medium transition ${
                anomalyFilter === 'ALL' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              All Alerts ({alerts.length})
            </button>
          </div>
        </div>

        {displayedAlerts.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400 bg-slate-800/30 rounded-xl border border-slate-800">
            <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
            No pending unusual transaction alerts. All outlays match your normal spending profile.
          </div>
        ) : (
          <div className="space-y-3">
            {displayedAlerts.map(alert => (
              <div
                key={alert.alert_id || alert.transaction_id}
                className={`p-4 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-4 transition ${
                  alert.is_dismissed
                    ? 'bg-slate-900/40 border-slate-800/50 opacity-60'
                    : 'bg-slate-800/40 border-slate-700/80 hover:border-slate-600'
                }`}
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="px-2 py-0.5 text-[10px] font-bold rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      {alert.label}
                    </span>
                    <span className={`px-2 py-0.5 text-[10px] font-bold rounded-md ${
                      alert.severity === 'HIGH'
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                    }`}>
                      {alert.severity} SEVERITY
                    </span>
                    <span className="text-xs text-slate-400 font-mono">{alert.date}</span>
                    <span className="text-xs font-semibold text-white">{alert.merchant}</span>
                    <span className="text-xs text-slate-400">({alert.category})</span>
                  </div>

                  <p className="text-xs text-slate-200">{alert.reason}</p>

                  <div className="flex items-center gap-3 pt-0.5">
                    <button
                      onClick={() => setWhyModal({
                        open: true,
                        title: `Explainable Statistical Reason: ${alert.merchant}`,
                        content: alert.why
                      })}
                      className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
                    >
                      <HelpCircle className="w-3.5 h-3.5" />
                      Why am I seeing this?
                    </button>
                    <button
                      onClick={() => setEvidenceDrawer({
                        open: true,
                        title: `Alert Source Transaction: ${alert.merchant}`,
                        queryParams: { metric: 'alert', alert_id: alert.alert_id }
                      })}
                      className="text-[11px] text-slate-400 hover:text-white flex items-center gap-1 font-medium"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      View Source Line
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-4 justify-between md:justify-end">
                  <span className="text-lg font-bold text-rose-400 font-mono">
                    {formatINR(alert.amount)}
                  </span>

                  {!alert.is_dismissed ? (
                    <button
                      disabled={dismissingId === alert.alert_id}
                      onClick={() => handleDismissAnomaly(alert.alert_id)}
                      className="px-3.5 py-2 text-xs font-semibold text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 rounded-xl flex items-center gap-1.5 transition"
                    >
                      <Check className="w-3.5 h-3.5" />
                      {dismissingId === alert.alert_id ? "Saving..." : "This was me"}
                    </button>
                  ) : (
                    <span className="text-xs text-slate-500 flex items-center gap-1">
                      <Check className="w-3.5 h-3.5 text-emerald-500" />
                      Dismissed by user
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* SECTION 2: Recurring Commitments */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Repeat className="w-5 h-5 text-indigo-400" />
              Detected Recurring Patterns
            </h2>
            <p className="text-xs text-slate-400">
              Repeating commitments identified through fuzzy merchant clustering and interval cadence
            </p>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 p-1 rounded-xl text-xs">
            {[
              { id: 'ALL', label: 'All Items' },
              { id: 'SUBSCRIPTION', label: 'Subscriptions' },
              { id: 'EMI', label: 'EMIs & Rent' },
              { id: 'FORGOTTEN', label: `Forgotten (${summary.potential_forgotten_count || 0})` },
            ].map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-3 py-1 rounded-lg font-medium transition ${
                  tab === t.id ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {filteredCommitments.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400 bg-slate-900/60 rounded-2xl border border-slate-800">
            No recurring commitments found under this filter.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCommitments.map(item => (
              <div
                key={item.id}
                className={`bg-slate-900/80 border rounded-2xl p-5 shadow-sm space-y-4 transition ${
                  item.is_potentially_forgotten
                    ? 'border-amber-500/40 bg-amber-500/5'
                    : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {item.classification}
                    </span>
                    <h3 className="text-base font-bold text-white mt-1.5">{item.merchant}</h3>
                    <span className="text-[11px] text-slate-400">{item.category}</span>
                  </div>

                  <span className="text-lg font-bold text-white font-mono">
                    {formatINR(item.average_amount)}
                    <span className="text-xs text-slate-400 font-normal">/{item.frequency.toLowerCase()}</span>
                  </span>
                </div>

                {item.is_potentially_forgotten && (
                  <div className="p-2.5 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-300 text-xs flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                    <span><strong>Potentially Forgotten:</strong> Continuous charges with low active interaction.</span>
                  </div>
                )}

                <div className="text-xs space-y-1.5 pt-2 border-t border-slate-800/80 text-slate-300">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Next Expected Date:</span>
                    <span className="font-mono text-white font-medium">{item.next_expected_date}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Estimated Annual Cost:</span>
                    <span className="font-mono text-indigo-300 font-medium">{formatINR(item.estimated_annual_cost)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Cadence Confidence:</span>
                    <span className="font-mono text-emerald-400 font-medium">
                      {Math.round(item.confidence * 100)}% ({item.transaction_count} instances)
                    </span>
                  </div>
                </div>

                <div className="pt-2 flex items-center justify-between border-t border-slate-800/60">
                  <button
                    onClick={() => setEvidenceDrawer({
                      open: true,
                      title: `${item.merchant} Recurring Source Rows`,
                      queryParams: { metric: 'recurring_item', merchant: item.merchant }
                    })}
                    className="text-[11px] text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    Audit Rows &rarr;
                  </button>
                  <button
                    onClick={() => setWhyModal({
                      open: true,
                      title: `Recurring Pattern Explanation: ${item.merchant}`,
                      content: item.explanation
                    })}
                    className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
                  >
                    <HelpCircle className="w-3.5 h-3.5" />
                    Why?
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* "Why am I seeing this?" Modal */}
      {whyModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
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
                className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg"
              >
                Understood
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Evidence Drawer */}
      <EvidenceDrawer
        isOpen={evidenceDrawer.open}
        onClose={() => setEvidenceDrawer({ open: false, title: '', queryParams: null })}
        title={evidenceDrawer.title}
        queryParams={evidenceDrawer.queryParams}
      />
    </div>
  );
}

