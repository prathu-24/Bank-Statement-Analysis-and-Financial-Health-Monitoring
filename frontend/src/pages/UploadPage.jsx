import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileText, CheckCircle, AlertCircle, ArrowRight, ShieldCheck, ShieldAlert, Zap, UserCheck, CreditCard } from 'lucide-react';
import { statementApi } from '../services/api';
import ColumnMappingModal from '../components/upload/ColumnMappingModal';
import ValidationReportView from '../components/upload/ValidationReportView';

export default function UploadPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const savedUserRaw = typeof window !== 'undefined' ? localStorage.getItem('finsight_user') : null;
  const savedUser = savedUserRaw ? JSON.parse(savedUserRaw) : null;

  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [currentFile, setCurrentFile] = useState(null);
  const [parseResult, setParseResult] = useState(null);
  const [isMappingModalOpen, setIsMappingModalOpen] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      processFile(files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files?.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = async (file) => {
    setError(null);
    setLoading(true);
    setCurrentFile(file);

    try {
      // Automatic detection: FinSight reads account holder name & account number directly from the statement
      const data = await statementApi.uploadStatement(file);
      setParseResult(data);
      if (data.needs_mapping) {
        setIsMappingModalOpen(true);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to upload and parse statement.");
    } finally {
      setLoading(false);
    }
  };

  const handleApplyMapping = async (mapping) => {
    if (!currentFile) return;
    setIsMappingModalOpen(false);
    setLoading(true);
    setError(null);

    try {
      const data = await statementApi.uploadWithMapping(currentFile, mapping);
      setParseResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to parse file with custom mapping.");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAndProceed = async () => {
    if (!parseResult || !parseResult.transactions) return;
    setLoading(true);
    setError(null);
    try {
      await statementApi.confirmTransactions(parseResult.transactions);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to save transactions.");
      setLoading(false);
    }
  };

  const handleReset = () => {
    setParseResult(null);
    setCurrentFile(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleLoadDemo = async (demoType) => {
    setError(null);
    setLoading(true);
    try {
      const data = await statementApi.loadDemoStatement(demoType);
      setParseResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to load demo statement.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider">
          <ShieldCheck className="w-4 h-4" />
          Bank Statement Intelligence & Privacy-First Engine
        </div>
        <h1 className="text-3xl font-bold text-white mt-1">Upload Bank Statement</h1>
        <p className="text-sm text-slate-400 mt-1 max-w-2xl">
          FinSight automatically parses Indian bank statements (HDFC, SBI, Generic CSVs, and PDFs), 
          validates double-entry arithmetic, categorizes cash-flows, and forecasts 30-day liquidity.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-center gap-3 text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <div>{error}</div>
        </div>
      )}

      {/* Main Upload or Report Area */}
      {!parseResult ? (
        <div className="space-y-6">
          {/* Automated Statement KYC & Anti-Fraud Shield */}
          <div className="bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900 border border-indigo-500/30 rounded-3xl p-5 shadow-xl">
            <div className="flex items-start gap-3.5">
              <div className="p-2.5 rounded-2xl bg-indigo-500/15 border border-indigo-500/30 text-indigo-400 mt-0.5">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div className="space-y-1 flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <span>Automated Statement Forensic & Account Shield</span>
                    <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2.5 py-0.5 rounded-full border border-emerald-500/30 font-semibold uppercase tracking-wider">
                      Auto-Detection Active
                    </span>
                  </h3>
                  <span className="text-[11px] text-indigo-300/80 font-mono hidden sm:inline-block">Zero Manual Typing</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  FinSight automatically reads the <strong className="text-slate-200">Account Holder Name</strong> and <strong className="text-slate-200">Bank Account Number</strong> directly from your uploaded statement file (PDF, CSV, Excel). Statements with dummy identities (e.g. <em>Fake Dummy User, John Doe, Test User</em>) or fake account sequences (e.g. <em>0000000000, 1234567890</em>) are <strong>strictly rejected</strong> and submission is blocked.
                </p>
              </div>
            </div>
          </div>

          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-3xl p-12 text-center cursor-pointer transition-all duration-200 ${
              isDragging
                ? 'border-indigo-500 bg-indigo-500/10 scale-[1.01]'
                : 'border-slate-700/80 hover:border-slate-500 bg-slate-900/40 hover:bg-slate-900/70'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".csv,.pdf"
              className="hidden"
            />
            <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 text-indigo-400 flex items-center justify-center mx-auto mb-4 border border-indigo-500/20">
              <UploadCloud className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-semibold text-white">
              {loading ? "Analyzing & Validating Statement..." : "Drag & drop statement, or browse"}
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Supports HDFC CSV, SBI CSV, Generic CSV, and Bank Statement PDFs (up to 25MB)
            </p>
            <div className="mt-4 flex items-center justify-center gap-2 text-[11px] text-slate-400">
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">Client-Side Memory Shield</span>
              <span>•</span>
              <span>Files deleted immediately after parsing</span>
            </div>
          </div>

          {/* Quick Demo Evaluation Datasets */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-indigo-400" />
                <h3 className="text-sm font-bold text-white">Instant Hackathon Demo Datasets</h3>
              </div>
              <span className="text-[11px] text-slate-400">Pre-generated 6-month synthetic statements</span>
            </div>

            <p className="text-xs text-slate-400">
              Test parsing, double-entry ledger validation, categorization, and forecasting with one click:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 pt-1">
              <button
                type="button"
                disabled={loading}
                onClick={() => handleLoadDemo('hdfc')}
                className="p-3 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 rounded-xl text-left transition space-y-1 group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white group-hover:text-indigo-300">HDFC CSV</span>
                  <span className="text-[10px] text-slate-400 uppercase">6 Mos</span>
                </div>
                <p className="text-[10px] text-slate-400">Narration, Chq/Ref, Withdrawals, Deposits</p>
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={() => handleLoadDemo('sbi')}
                className="p-3 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 rounded-xl text-left transition space-y-1 group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white group-hover:text-indigo-300">SBI CSV</span>
                  <span className="text-[10px] text-slate-400 uppercase">6 Mos</span>
                </div>
                <p className="text-[10px] text-slate-400">Txn Date, Particulars, Ref, Debit, Credit</p>
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={() => handleLoadDemo('generic')}
                className="p-3 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 rounded-xl text-left transition space-y-1 group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white group-hover:text-indigo-300">Generic CSV</span>
                  <span className="text-[10px] text-slate-400 uppercase">Standard</span>
                </div>
                <p className="text-[10px] text-slate-400">Standard ledger format with 5 columns</p>
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={() => handleLoadDemo('pdf')}
                className="p-3 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 rounded-xl text-left transition space-y-1 group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white group-hover:text-indigo-300">Statement PDF</span>
                  <span className="text-[10px] text-emerald-400 uppercase font-semibold">Tabular</span>
                </div>
                <p className="text-[10px] text-slate-400">Multi-page National Bank of India PDF</p>
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={() => handleLoadDemo('broken')}
                className="p-3 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 rounded-xl text-left transition space-y-1 group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-amber-300 group-hover:text-amber-200">Broken CSV</span>
                  <span className="text-[10px] text-amber-400 uppercase font-bold">Audit Demo</span>
                </div>
                <p className="text-[10px] text-amber-300/70">Math errors, invalid dates, duplicates</p>
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={() => handleLoadDemo('fake')}
                className="p-3 bg-rose-500/15 hover:bg-rose-500/25 border-2 border-rose-500/50 rounded-xl text-left transition space-y-1 group shadow-lg shadow-rose-950/40"
                title="Loads a statement with 'Fake Dummy User' and 0000000000 to verify automatic fraud rejection"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-rose-300 group-hover:text-rose-100 flex items-center gap-1">
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                    Fake A/C
                  </span>
                  <span className="text-[10px] text-rose-300 uppercase font-black px-1.5 py-0.5 bg-rose-500/30 rounded border border-rose-500/40">REJECT</span>
                </div>
                <p className="text-[10px] text-rose-300/80">Auto-detects fake credentials and rejects statement</p>
              </button>
            </div>

            {/* Benchmark Demographic Personas */}
            <div className="pt-2 border-t border-slate-800">
              <span className="text-[11px] font-bold text-indigo-400 uppercase block mb-2">
                Evaluated Demographic Personas (6-Month Benchmarks):
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleLoadDemo('salaried')}
                  className="p-3 bg-slate-900 hover:bg-slate-800 border border-slate-700/80 hover:border-indigo-500/50 rounded-xl text-left transition space-y-1 group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white group-hover:text-indigo-300">Salaried Pro</span>
                    <span className="text-[10px] text-indigo-400 uppercase font-semibold">₹85k/mo</span>
                  </div>
                  <p className="text-[10px] text-slate-400">Fixed salary, rent, home EMI, Cult.fit, planted jewelry spike</p>
                </button>

                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleLoadDemo('gig_worker')}
                  className="p-3 bg-slate-900 hover:bg-slate-800 border border-slate-700/80 hover:border-indigo-500/50 rounded-xl text-left transition space-y-1 group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white group-hover:text-indigo-300">Gig Worker</span>
                    <span className="text-[10px] text-amber-400 uppercase font-semibold">Irregular</span>
                  </div>
                  <p className="text-[10px] text-slate-400">Zomato/Uber payouts, fuel debits, bike loan EMI, engine overhaul</p>
                </button>

                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleLoadDemo('student')}
                  className="p-3 bg-slate-900 hover:bg-slate-800 border border-slate-700/80 hover:border-indigo-500/50 rounded-xl text-left transition space-y-1 group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white group-hover:text-indigo-300">College Student</span>
                    <span className="text-[10px] text-emerald-400 uppercase font-semibold">₹15k allowance</span>
                  </div>
                  <p className="text-[10px] text-slate-400">Parental allowance, PG rent, campus canteen UPI, exam fees</p>
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <ValidationReportView
          report={parseResult.validation_report}
          filename={parseResult.filename}
          detectedFormat={parseResult.detected_format}
          accountVerification={parseResult.account_verification}
          onConfirm={handleConfirmAndProceed}
          onReset={handleReset}
        />
      )}

      {/* Column Mapping Modal for Unknown formats */}
      <ColumnMappingModal
        headers={parseResult?.detected_headers || []}
        sampleRows={parseResult?.sample_rows || []}
        isOpen={isMappingModalOpen}
        onClose={() => setIsMappingModalOpen(false)}
        onApply={handleApplyMapping}
      />
    </div>
  );
}

