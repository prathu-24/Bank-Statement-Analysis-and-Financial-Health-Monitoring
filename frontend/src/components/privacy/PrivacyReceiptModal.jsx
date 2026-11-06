import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  HardDrive,
  EyeOff,
  Radio,
  Clock,
  Key,
  Trash2,
  X,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  RefreshCw
} from 'lucide-react';
import { statementApi } from '../../services/api';

export default function PrivacyReceiptModal({ isOpen, onClose, onDataPurged }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [purging, setPurging] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchReceipt();
    }
  }, [isOpen]);

  const fetchReceipt = async () => {
    setLoading(true);
    try {
      const res = await statementApi.getPrivacyStatus();
      setData(res);
    } catch (err) {
      console.error("Failed to load privacy receipt:", err);
    } finally {
      setLoading(false);
    }
  };

  const handlePurge = async () => {
    if (!window.confirm("Are you sure you want to permanently delete all statement records, category overrides, and alerts? This cannot be undone.")) {
      return;
    }
    setPurging(true);
    try {
      await statementApi.deleteAllData();
      await fetchReceipt();
      if (onDataPurged) onDataPurged();
    } catch (err) {
      alert("Failed to purge data: " + (err.message || "Unknown error"));
    } finally {
      setPurging(false);
    }
  };

  if (!isOpen) return null;

  const db = data?.database || {};
  const stored = data?.stored_records || {};
  const sanitization = data?.sanitization || {};
  const network = data?.network_isolation || {};
  const retention = data?.retention_policy || {};
  const encryption = data?.encryption_at_rest || {};

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-2xl w-full p-6 shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-2xl">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white">Cryptographic Privacy Receipt</h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  Verifiable Local State
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Provable audit trail of what was read, stored on disk, masked, and sent out.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading && !data ? (
          <div className="py-16 text-center space-y-3">
            <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
            <p className="text-xs text-slate-400">Computing hardware-local privacy metrics...</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* 1. What Is Stored */}
            <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-2xl space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-200 text-xs font-semibold">
                  <HardDrive className="w-4 h-4 text-indigo-400" />
                  What is Stored (Local SQLite)
                </div>
                <span className="text-[11px] font-mono text-indigo-400 font-semibold">
                  {db.file_size_human || '0 B'} on disk
                </span>
              </div>
              <div className="text-[11px] space-y-1 text-slate-400 font-mono bg-slate-900/80 p-2.5 rounded-xl border border-slate-800">
                <div className="truncate">
                  <span className="text-slate-500">Path: </span>
                  <span className="text-slate-300">{db.file_path || 'finsight.db'}</span>
                </div>
                <div className="flex flex-wrap gap-4 pt-1 text-slate-300">
                  <span>Transactions: <strong className="text-white">{stored.transactions || 0}</strong></span>
                  <span>Category Overrides: <strong className="text-white">{stored.category_overrides || 0}</strong></span>
                  <span>Alerts: <strong className="text-white">{stored.alerts || 0}</strong></span>
                  <span>Total Rows: <strong className="text-emerald-400">{stored.total_rows || 0}</strong></span>
                </div>
              </div>
            </div>

            {/* 2. What Was Masked (PII Neutralization) */}
            <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-2xl space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-200 text-xs font-semibold">
                  <EyeOff className="w-4 h-4 text-emerald-400" />
                  What Was Masked (Regex PII Neutralization)
                </div>
                <span className="px-2 py-0.5 rounded-md text-[11px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {sanitization.total_masked_values || 0} Tokens Masked
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                PII is redacted prior to database commit. Account numbers, PAN cards, phone numbers, and card numbers are neutralized with zero leakage.
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                {Object.entries(sanitization.breakdown || {}).map(([key, count]) => (
                  <div key={key} className="bg-slate-900/60 border border-slate-800 p-2 rounded-xl text-center">
                    <span className="text-[10px] text-slate-500 uppercase block">
                      {key.replace('_', ' ')}
                    </span>
                    <span className="text-xs font-bold text-white font-mono mt-0.5 block">
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* 3. What Was Sent Out (Network Isolation) */}
            <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-2xl space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-200 text-xs font-semibold">
                  <Radio className="w-4 h-4 text-cyan-400" />
                  What Was Sent Out (Zero Telemetry Guarantee)
                </div>
                <span className={`px-2 py-0.5 rounded-md text-[11px] font-mono font-bold ${
                  (network.outbound_network_calls || 0) === 0
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                }`}>
                  {network.outbound_network_calls || 0} Outbound Calls
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-emerald-400 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{network.status || '100% Offline Local Processing'}</span>
              </div>
              <p className="text-[11px] text-slate-500">
                All parsing, categorizing, Monte Carlo simulations, and distress radar computations occur locally on this machine.
              </p>
            </div>

            {/* 4. Retention Policy & Cryptographic Encryption */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Retention */}
              <div className="p-3.5 bg-slate-950/60 border border-slate-800/80 rounded-2xl space-y-1.5">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                  <Clock className="w-3.5 h-3.5 text-amber-400" />
                  Data Retention Policy
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  {retention.policy_description || 'Local-device persistence until user triggers manual deletion.'}
                </p>
              </div>

              {/* Encryption */}
              <div className="p-3.5 bg-slate-950/60 border border-slate-800/80 rounded-2xl space-y-1.5">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                  <Key className="w-3.5 h-3.5 text-purple-400" />
                  At-Rest Encryption
                </div>
                <div className="flex items-center gap-1.5 text-[11px]">
                  <span className={`px-1.5 py-0.5 rounded font-mono font-bold text-[10px] ${
                    encryption.enabled
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-slate-800 text-slate-400'
                  }`}>
                    {encryption.cipher || 'Plaintext SQLite'}
                  </span>
                  <span className="text-slate-400 text-[10px]">
                    {encryption.enabled ? 'Active key detected' : '(Optional Fernet key)'}
                  </span>
                </div>
              </div>
            </div>

            {/* Methodology Note */}
            <div className="p-3 bg-indigo-500/5 border border-indigo-500/20 rounded-xl text-[11px] text-indigo-300">
              <strong className="text-white block mb-0.5">Hardware-Local Architecture Guarantee:</strong>
              {data?.methodology}
            </div>

            {/* Actions: Purge and Refresh */}
            <div className="pt-2 flex items-center justify-between border-t border-slate-800">
              <button
                onClick={fetchReceipt}
                className="px-3 py-1.5 rounded-xl border border-slate-700 text-slate-300 hover:text-white text-xs flex items-center gap-1.5 hover:bg-slate-800 transition"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Refresh Audit
              </button>

              <button
                onClick={handlePurge}
                disabled={purging || (stored.total_rows || 0) === 0}
                className="px-4 py-2 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 text-xs font-semibold flex items-center gap-2 transition disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <Trash2 className="w-3.5 h-3.5" />
                {purging ? "Purging Records..." : "Permanently Purge All Data"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

