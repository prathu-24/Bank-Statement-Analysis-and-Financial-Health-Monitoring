import React, { useState } from 'react';
import { CheckCircle2, AlertTriangle, XCircle, ArrowRight, RefreshCw, FileText, Scale, ShieldCheck, ShieldAlert } from 'lucide-react';

export default function ValidationReportView({ report, filename, detectedFormat, accountVerification, onConfirm, onReset }) {
  const [filter, setFilter] = useState('ALL');

  if (!report) return null;

  const isFakeAccount = accountVerification && accountVerification.is_authentic === false;
  const isStatementValid = report.is_valid && !isFakeAccount;

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
      {/* Account Verification & Fraud Shield Banner */}
      {accountVerification && (
        isFakeAccount ? (
          <div className="p-5 bg-rose-500/15 border-2 border-rose-500/50 rounded-2xl flex items-start gap-4 text-rose-200 shadow-xl shadow-rose-950/40">
            <div className="p-2.5 rounded-xl bg-rose-900/50 border border-rose-500/40 mt-0.5">
              <ShieldAlert className="w-6 h-6 text-rose-400" />
            </div>
            <div className="space-y-1.5 flex-1">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-base text-white flex items-center gap-2">
                  <span>STATEMENT REJECTED: Fake / Fraudulent Account Detected</span>
                </h3>
                <span className="text-[11px] bg-rose-500/30 text-rose-200 px-3 py-1 rounded-full border border-rose-500/40 uppercase font-extrabold tracking-wider">
                  Fraud Shield Blocked
                </span>
              </div>
              <p className="text-xs text-rose-300 font-medium">
                {accountVerification.message}
              </p>
              <div className="text-[11px] text-rose-300/80 font-mono bg-slate-950/60 p-2 rounded-lg border border-rose-500/20 mt-1 inline-block">
                Flagged Holder: <strong>{accountVerification.account_holder_name}</strong> &bull; A/C: <strong>{accountVerification.account_number}</strong>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl flex items-center justify-between text-emerald-200 text-xs">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-emerald-950/50 border border-emerald-500/30">
                <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0" />
              </div>
              <div>
                <div className="font-bold text-white text-sm">Account Identity Verified & Authentic</div>
                <div className="text-slate-400 text-xs mt-0.5">
                  Account Holder: <strong className="text-slate-200">{accountVerification.account_holder_name}</strong> &bull; A/C No: <strong className="text-slate-200">{accountVerification.account_number}</strong>
                </div>
              </div>
            </div>
            <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 rounded-full font-bold text-[11px]">
              KYC AUTHENTIC ✓
            </span>
          </div>
        )
      )}

      {/* Status Banner */}
      <div className={`p-5 rounded-2xl border flex items-start justify-between ${
        isStatementValid 
          ? warning_count === 0 
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
            : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
      }`}>
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-slate-900/60 mt-1">
            {isStatementValid ? (
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
                {isStatementValid 
                  ? (warning_count === 0 ? "Statement Validated Perfectly" : "Validated with Warnings") 
                  : "Statement Rejected / Validation Failed"}
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
          {isStatementValid ? (
            <button
              onClick={onConfirm}
              className="px-5 py-2.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition"
            >
              Confirm & Analyze
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              disabled
              className="px-5 py-2.5 text-xs font-bold text-rose-300 bg-rose-500/20 border border-rose-500/40 rounded-lg flex items-center gap-2 cursor-not-allowed opacity-80"
              title="Submission blocked: The statement has fatal validation errors or fake account details."
            >
              <XCircle className="w-4 h-4" />
              Submission Blocked (Rejected)
            </button>
          )}
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

      {/* Statement-Level Ledger Reconciliation Audit */}
      <div className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs ${
        report.statement_balance_reconciled !== false
          ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-300'
          : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
      }`}>
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${
            report.statement_balance_reconciled !== false ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
          }`}>
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <span className="font-semibold text-white block">
              {report.statement_balance_reconciled !== false
                ? "Statement-Level Ledger Balance: Reconciled"
                : "Statement-Level Ledger Discrepancy Detected"}
            </span>
            <p className="text-slate-400 mt-0.5">
              Opening: <strong className="text-slate-200">₹{Number(report.opening_balance || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong>
              {' '}+ Credits: <strong className="text-emerald-400">₹{Number(report.total_credits || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong>
              {' '}- Debits: <strong className="text-rose-400">₹{Number(report.total_debits || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong>
              {' '}≈ Calculated Closing: <strong className="text-white">₹{Number(report.calculated_closing_balance || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong>
            </p>
          </div>
        </div>

        <div className="text-right">
          <span className="text-slate-400 block text-[11px]">Recorded Closing Balance:</span>
          <span className="font-mono font-bold text-white text-sm">
            ₹{Number(report.closing_balance || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
          {report.statement_balance_discrepancy > 0 && (
            <span className="text-[10px] text-rose-400 font-semibold block">
              Drift: ₹{Number(report.statement_balance_discrepancy).toFixed(2)}
            </span>
          )}
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

