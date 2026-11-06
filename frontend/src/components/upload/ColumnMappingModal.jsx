import React, { useState } from 'react';
import { Columns3, AlertCircle, Check, X } from 'lucide-react';

export default function ColumnMappingModal({ headers = [], sampleRows = [], isOpen, onClose, onApply }) {
  const [dateCol, setDateCol] = useState(headers.find(h => /date/i.test(h)) || headers[0] || '');
  const [descCol, setDescCol] = useState(headers.find(h => /desc|narration|memo|particular/i.test(h)) || headers[1] || '');
  const [debitCol, setDebitCol] = useState(headers.find(h => /debit|withdrawal|spent/i.test(h)) || '');
  const [creditCol, setCreditCol] = useState(headers.find(h => /credit|deposit|received/i.test(h)) || '');
  const [amountCol, setAmountCol] = useState(headers.find(h => /^amount$/i.test(h)) || '');
  const [balanceCol, setBalanceCol] = useState(headers.find(h => /balance|bal/i.test(h)) || headers[headers.length - 1] || '');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!dateCol || !descCol || !balanceCol || (!debitCol && !creditCol && !amountCol)) {
      alert("Please map at least Date, Description, Balance, and an Amount column.");
      return;
    }
    onApply({
      date_col: dateCol,
      description_col: descCol,
      debit_col: debitCol || null,
      credit_col: creditCol || null,
      amount_col: amountCol || null,
      balance_col: balanceCol,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-2xl w-full p-6 shadow-2xl overflow-y-auto max-h-[90vh]">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
              <Columns3 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Custom Column Mapping</h3>
              <p className="text-xs text-slate-400">Match your statement's columns with FinSight's schema</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Date Column <span className="text-rose-400">*</span>
              </label>
              <select
                value={dateCol}
                onChange={(e) => setDateCol(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="">Select Date Column</option>
                {headers.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Description / Narration <span className="text-rose-400">*</span>
              </label>
              <select
                value={descCol}
                onChange={(e) => setDescCol(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="">Select Description Column</option>
                {headers.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Debit / Withdrawal</label>
              <select
                value={debitCol}
                onChange={(e) => setDebitCol(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="">(Optional if Single Amount column)</option>
                {headers.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Credit / Deposit</label>
              <select
                value={creditCol}
                onChange={(e) => setCreditCol(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="">(Optional if Single Amount column)</option>
                {headers.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Single Amount Column (Signed +/-)
              </label>
              <select
                value={amountCol}
                onChange={(e) => setAmountCol(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="">(None - separate Debit/Credit)</option>
                {headers.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Account Balance <span className="text-rose-400">*</span>
              </label>
              <select
                value={balanceCol}
                onChange={(e) => setBalanceCol(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="">Select Balance Column</option>
                {headers.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>
          </div>

          {/* Sample rows preview */}
          {sampleRows.length > 0 && (
            <div className="mt-4">
              <span className="text-xs text-slate-400 font-medium">Data Preview (First {sampleRows.length} rows):</span>
              <div className="mt-1 overflow-x-auto border border-slate-800 rounded-lg">
                <table className="min-w-full text-xs text-left text-slate-300">
                  <thead className="bg-slate-800/80 text-slate-400 uppercase">
                    <tr>
                      {headers.slice(0, 6).map(h => (
                        <th key={h} className="px-3 py-2">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sampleRows.map((r, i) => (
                      <tr key={i} className="border-t border-slate-800 hover:bg-slate-800/30">
                        {headers.slice(0, 6).map(h => (
                          <td key={h} className="px-3 py-2 truncate max-w-[150px]">{r[h] ?? ''}</td>
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
              className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition"
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

