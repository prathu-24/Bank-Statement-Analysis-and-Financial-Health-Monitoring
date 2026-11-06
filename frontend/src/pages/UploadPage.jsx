import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileText, CheckCircle, AlertCircle, ArrowRight, ShieldCheck, Zap } from 'lucide-react';
import { statementApi } from '../services/api';
import ColumnMappingModal from '../components/upload/ColumnMappingModal';
import ValidationReportView from '../components/upload/ValidationReportView';

export default function UploadPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

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
        </div>
      ) : (
        <ValidationReportView
          report={parseResult.validation_report}
          filename={parseResult.filename}
          detectedFormat={parseResult.detected_format}
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

