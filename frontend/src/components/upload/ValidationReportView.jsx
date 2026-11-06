import React, { useState } from 'react';
import { CheckCircle2, AlertTriangle, XCircle, ArrowRight, RefreshCw, FileText, Scale } from 'lucide-react';

export default function ValidationReportView({ report, filename, detectedFormat, onConfirm, onReset }) {
  const [filter, setFilter] = useState('ALL');

  if (!report) return null;

  const {
    is_valid,
    total_rows,
    valid_rows,
    error_count,
    warning_count,
    duplicate_count,
    balance_mismatch_count,
    issues = [],
    summary
  } = report;

  const filteredIssues = issues.filter(iss => {
    if (filter === 'ALL') return true;
    return iss.level === filter;
  });

  return (
    <div className="space-y-6">
      {/* Status Banner */}
      <div className={`p-5 rounded-2xl border flex items-start justify-between ${
        is_valid 
          ? warning_count === 0 
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
            : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
      }`}>
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-slate-900/60 mt-1">
            {is_valid ? (
              warning_count === 0 ? (
                <CheckCircle2 className="w-8 h-8 text-emerald-400" />
              ) : (
                <AlertTriangle className="w-8 h-8 text-amber-400" />
              )
            ) : (
              <XCircle className="w-8 h-8 text-rose-400" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-white">
                {is_valid 
                  ? (warning_count === 0 ? "Statement Validated Perfectly" : "Validated with Warnings") 
                  : "Validation Issues Encountered"}
              </h2>
              <span className="text-xs uppercase px-2.5 py-0.5 rounded-full font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                {detectedFormat.toUpperCase()} Format
              </span>
            </div>
            <p className="text-sm mt-1 text-slate-300 max-w-2xl">{summary}</p>
            <div className="flex items-center gap-4 text-xs text-slate-400 mt-2">
              <span>File: <strong className="text-slate-200">{filename}</strong></span>
              {report.date_range_start && (
                <span>Period: <strong className="text-slate-200">{report.date_range_start}</strong> to <strong className="text-slate-200">{report.date_range_end}</strong></span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onReset}
            className="px-4 py-2 text-xs font-semibold text-slate-300 bg-slate-800/80 hover:bg-slate-700 rounded-lg flex items-center gap-2 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Upload Another
          </button>
          <button
            onClick={onConfirm}
            className="px-5 py-2.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition"
          >
            Confirm & Analyze
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-slate-800/50 border border-slate-700/60 p-4 rounded-xl">
          <span className="text-xs text-slate-400 block">Total Parsed</span>
          <span className="text-2xl font-bold text-white mt-1 block">{total_rows}</span>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/60 p-4 rounded-xl">
          <span className="text-xs text-slate-400 block">Valid Rows</span>
          <span className="text-2xl font-bold text-emerald-400 mt-1 block">{valid_rows}</span>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/60 p-4 rounded-xl">
          <span className="text-xs text-slate-400 block">Fatal Errors</span>
          <span className={`text-2xl font-bold mt-1 block ${error_count > 0 ? 'text-rose-400' : 'text-slate-300'}`}>
            {error_count}
          </span>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/60 p-4 rounded-xl">
          <span className="text-xs text-slate-400 block">Warnings</span>
          <span className={`text-2xl font-bold mt-1 block ${warning_count > 0 ? 'text-amber-400' : 'text-slate-300'}`}>
            {warning_count}
          </span>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/60 p-4 rounded-xl">
          <span className="text-xs text-slate-400 block">Duplicates</span>
          <span className="text-2xl font-bold text-amber-400 mt-1 block">{duplicate_count}</span>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/60 p-4 rounded-xl">
          <span className="text-xs text-slate-400 block">Balance Drifts</span>
          <span className={`text-2xl font-bold mt-1 block ${balance_mismatch_count > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
            {balance_mismatch_count}
          </span>
        </div>
      </div>

      {/* Arithmetic Verification Details */}
      <div className="p-4 bg-slate-900/70 border border-slate-800 rounded-xl flex items-center gap-3">
        <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
          <Scale className="w-5 h-5" />
        </div>
        <div className="text-xs text-slate-300">
          <strong className="text-white block font-medium">Mathematical Direction Verification:</strong>
          Verified ledger balance continuity using formula: 
          <code className="mx-1 px-1.5 py-0.5 bg-slate-800 rounded text-indigo-300 font-mono">Previous Balance + Credit - Debit ≈ Current Balance</code> 
          with ₹1.00 rounding tolerance. No valid transactions were discarded.
        </div>
      </div>

      {/* Issues Table */}
      {issues.length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-indigo-400" />
              Validation Audit Log ({issues.length} notifications)
            </h3>
            <div className="flex gap-1.5 bg-slate-800/60 p-1 rounded-lg text-xs">
              {['ALL', 'ERROR', 'WARNING'].map(lvl => (
                <button
                  key={lvl}
                  onClick={() => setFilter(lvl)}
                  className={`px-3 py-1 rounded-md font-medium transition ${
                    filter === lvl ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {lvl}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-xs text-left">
              <thead className="bg-slate-800/60 text-slate-400 uppercase font-medium">
                <tr>
                  <th className="px-3 py-2.5 rounded-l-lg">Severity</th>
                  <th className="px-3 py-2.5">Code</th>
                  <th className="px-3 py-2.5">Row</th>
                  <th className="px-3 py-2.5 rounded-r-lg">Details & Evidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {filteredIssues.map((iss, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="px-3 py-2.5">
                      <span className={`px-2 py-0.5 rounded-full font-semibold text-[10px] ${
                        iss.level === 'ERROR'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : iss.level === 'WARNING'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                      }`}>
                        {iss.level}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 font-mono text-slate-300">{iss.code}</td>
                    <td className="px-3 py-2.5 text-slate-400">{iss.row_number ?? 'N/A'}</td>
                    <td className="px-3 py-2.5 text-slate-200">{iss.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

