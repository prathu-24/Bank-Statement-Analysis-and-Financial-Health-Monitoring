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

  const [accountHolderName, setAccountHolderName] = useState(savedUser?.name || 'Arjun Verma');
  const [accountNumber, setAccountNumber] = useState('');
  const [requireKYCCheck, setRequireKYCCheck] = useState(true);

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
      const data = await statementApi.uploadStatement(
        file,
        requireKYCCheck ? accountHolderName : null,
        requireKYCCheck ? accountNumber : null
      );
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
      const data = await statementApi.uploadWithMapping(
        currentFile,
        mapping,
        requireKYCCheck ? accountHolderName : null,
        requireKYCCheck ? accountNumber : null
      );
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
          {/* Account Holder Verification & Fraud Shield */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/30">
                  <ShieldCheck className="w-5 h-5 text-indigo-400" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <span>Account Holder & Identity Verification</span>
                    <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-2.5 py-0.5 rounded-full border border-indigo-500/30 font-semibold uppercase tracking-wider">
                      Anti-Fraud KYC Shield
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Validates statement authenticity against account holder name and bank account number. Rejects fake, dummy, or forged entries.
                  </p>
                </div>
              </div>
              <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-300">
                <input
                  type="checkbox"
                  checked={requireKYCCheck}
                  onChange={(e) => setRequireKYCCheck(e.target.checked)}
                  className="w-4 h-4 rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500"
                />
                <span>Enforce Account Validation</span>
              </label>
            </div>

            {requireKYCCheck && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-300 flex items-center justify-between">
                    <span>Expected Account Holder Name:</span>
                    <span className="text-[10px] text-slate-400">Rejects dummy/test identities</span>
                  </label>
                  <div className="relative">
                    <UserCheck className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
                    <input
                      type="text"
                      value={accountHolderName}
                      onChange={(e) => setAccountHolderName(e.target.value)}
                      placeholder="e.g. Arjun Verma"
                      className="w-full pl-9 pr-3 py-2 bg-slate-950/70 border border-slate-700/80 rounded-xl text-sm text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 transition"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-300 flex items-center justify-between">
                    <span>Expected Bank Account Number:</span>
                    <span className="text-[10px] text-slate-400">9–18 numeric digits</span>
                  </label>
                  <div className="relative">
                    <CreditCard className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
                    <input
                      type="text"
                      value={accountNumber}
                      onChange={(e) => setAccountNumber(e.target.value)}
                      placeholder="e.g. 982014902144 (or leave blank to auto-detect from statement)"
                      className="w-full pl-9 pr-3 py-2 bg-slate-950/70 border border-slate-700/80 rounded-xl text-sm text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 transition"
                    />
                  </div>
                </div>

                {/* Quick Test Profiles */}
                <div className="md:col-span-2 flex flex-wrap items-center gap-2 pt-1 text-xs">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Test Quick Profiles:</span>
                  <button
                    type="button"
                    onClick={() => { setAccountHolderName('Arjun Verma'); setAccountNumber('982014902144'); }}
                    className="px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[11px] font-medium transition"
                  >
                    ✓ Authentic: Arjun Verma (Valid A/C)
                  </button>
                  <button
                    type="button"
                    onClick={() => { setAccountHolderName('Pooja Sharma'); setAccountNumber('002301589123'); }}
                    className="px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[11px] font-medium transition"
                  >
                    ✓ Authentic: Pooja Sharma (ICICI A/C)
                  </button>
                  <button
                    type="button"
                    onClick={() => { setAccountHolderName('Fake User'); setAccountNumber('0000000000'); }}
                    className="px-2.5 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[11px] font-medium transition"
                    title="Simulate fake identity to test automatic rejection"
                  >
                    ⚠ Test Fake: 'Fake User' & 0000000000 (Triggers Rejection)
                  </button>
                  <button
                    type="button"
                    onClick={() => { setAccountHolderName('John Doe'); setAccountNumber('1234567890'); }}
                    className="px-2.5 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[11px] font-medium transition"
                    title="Simulate sequential dummy number to test automatic rejection"
                  >
                    ⚠ Test Fake: 'John Doe' & 1234567890 (Triggers Rejection)
                  </button>
                </div>
              </div>
            )}
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

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 pt-1">
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
                className="p-3 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 rounded-xl text-left transition space-y-1 group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-rose-300 group-hover:text-rose-200">Broken CSV</span>
                  <span className="text-[10px] text-rose-400 uppercase font-bold">Audit Demo</span>
                </div>
                <p className="text-[10px] text-rose-300/70">Deliberate math errors, invalid dates, duplicates</p>
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

