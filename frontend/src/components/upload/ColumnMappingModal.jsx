import React, { useState, useEffect } from 'react';
import { Columns3, Sparkles, Check, X, AlertCircle } from 'lucide-react';

export default function ColumnMappingModal({ headers = [], sampleRows = [], isOpen, onClose, onApply }) {
  const [dateCol, setDateCol] = useState('');
  const [descCol, setDescCol] = useState('');
  const [debitCol, setDebitCol] = useState('');
  const [creditCol, setCreditCol] = useState('');
  const [amountCol, setAmountCol] = useState('');
  const [balanceCol, setBalanceCol] = useState('');
  const [validationError, setValidationError] = useState('');

  const autoDetectColumns = (cols) => {
    if (!cols || cols.length === 0) return;

    const findMatch = (pattern) => cols.find(h => pattern.test(h)) || '';

    const dCol = findMatch(/date|dt\b|time|day|period|timestamp|posting|value/i) || cols[0] || '';
    const dsCol = findMatch(/desc|narration|particular|memo|detail|remark|txn|trans|payee|party|reference/i) || (cols.length > 1 ? cols[1] : '');
    const drCol = findMatch(/debit|withdrawal|spent|dr\b|outflow|paid\s*out|payment/i);
    const crCol = findMatch(/credit|deposit|received|cr\b|inflow|paid\s*in|receipt/i);
    const amtCol = findMatch(/^amount$|^amt$|txn\s*amount|net\s*amount/i);
    const bCol = findMatch(/balance|bal\b|closing/i) || (cols.length > 2 ? cols[cols.length - 1] : '(AUTO_COMPUTE)');

    setDateCol(dCol);
    setDescCol(dsCol);
    setDebitCol(drCol);
    setCreditCol(crCol);
    setAmountCol(amtCol);
    setBalanceCol(bCol);
    setValidationError('');
  };

  useEffect(() => {
    if (isOpen && headers && headers.length > 0) {
      autoDetectColumns(headers);
    }
  }, [isOpen, headers]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!dateCol) {
      setValidationError("Please select a Date column.");
      return;
    }
    if (!descCol) {
      setValidationError("Please select a Description / Narration column.");
      return;
    }
    if (!debitCol && !creditCol && !amountCol) {
      setValidationError("Please map either Debit & Credit columns, or a single Signed Amount column.");
      return;
    }

    setValidationError('');
    onApply({
      date_col: dateCol,
      description_col: descCol,
      debit_col: debitCol || null,
      credit_col: creditCol || null,
      amount_col: amountCol || null,
      balance_col: (balanceCol === '(AUTO_COMPUTE)' || !balanceCol) ? null : balanceCol,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-6 shadow-2xl overflow-y-auto max-h-[92vh] space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/15 text-indigo-400 rounded-xl border border-indigo-500/30">
              <Columns3 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Custom Column Mapping</h3>
              <p className="text-xs text-slate-400">Match your statement's columns with FinSight's schema</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => autoDetectColumns(headers)}
              className="px-3 py-1.5 text-xs font-semibold text-indigo-300 hover:text-white bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 rounded-lg flex items-center gap-1.5 transition"
              title="Automatically re-detect best column matches"
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              Auto-Detect
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {validationError && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-center gap-2.5 text-rose-300 text-xs">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{validationError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Date Column <span className="text-rose-400">*</span>
              </label>
              <select
                value={dateCol}
                onChange={(e) => { setDateCol(e.target.value); setValidationError(''); }}
                className="w-full bg-slate-950/80 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 transition"
              >
                <option value="">Select Date Column</option>
                {headers.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Description / Narration <span className="text-rose-400">*</span>
              </label>
              <select
                value={descCol}
                onChange={(e) => { setDescCol(e.target.value); setValidationError(''); }}
                className="w-full bg-slate-950/80 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 transition"
              >
                <option value="">Select Description Column</option>
                {headers.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Debit / Withdrawal</label>
              <select
                value={debitCol}
                onChange={(e) => { setDebitCol(e.target.value); setValidationError(''); }}
                className="w-full bg-slate-950/80 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 transition"
              >
                <option value="">(Optional if Single Amount column)</option>
                {headers.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Credit / Deposit</label>
              <select
                value={creditCol}
                onChange={(e) => { setCreditCol(e.target.value); setValidationError(''); }}
                className="w-full bg-slate-950/80 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 transition"
              >
                <option value="">(Optional if Single Amount column)</option>
                {headers.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Single Amount Column (Signed +/-)
              </label>
              <select
                value={amountCol}
                onChange={(e) => { setAmountCol(e.target.value); setValidationError(''); }}
                className="w-full bg-slate-950/80 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 transition"
              >
                <option value="">(None - separate Debit/Credit)</option>
                {headers.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Account Balance
              </label>
              <select
                value={balanceCol}
                onChange={(e) => setBalanceCol(e.target.value)}
                className="w-full bg-slate-950/80 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 transition"
              >
                <option value="(AUTO_COMPUTE)">Auto-compute running balance (if no balance column)</option>
                {headers.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>
          </div>

          {/* Sample rows preview */}
          {sampleRows.length > 0 && (
            <div className="pt-2">
              <span className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider block mb-1.5">
                Data Preview (First {sampleRows.length} rows):
              </span>
              <div className="overflow-x-auto border border-slate-800 rounded-xl bg-slate-950/50">
                <table className="min-w-full text-xs text-left text-slate-300">
                  <thead className="bg-slate-800/80 text-slate-400 uppercase font-semibold text-[10px]">
                    <tr>
                      {headers.slice(0, 7).map(h => (
                        <th key={h} className="px-3 py-2 whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sampleRows.map((r, i) => (
                      <tr key={i} className="border-t border-slate-800/80 hover:bg-slate-800/30">
                        {headers.slice(0, 7).map(h => (
                          <td key={h} className="px-3 py-1.5 truncate max-w-[160px] text-slate-300 font-mono text-[11px]">
                            {r[h] ?? ''}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition"
            >
              <Check className="w-4 h-4" />
              Apply Mapping & Parse
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
