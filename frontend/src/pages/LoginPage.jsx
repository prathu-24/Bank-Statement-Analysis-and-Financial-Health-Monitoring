import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  CreditCard,
  Lock,
  Mail,
  Eye,
  EyeOff,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  UserCheck,
  Briefcase,
  Bike,
  GraduationCap
} from 'lucide-react';
import { statementApi } from '../services/api';

const DEMO_PRESETS = [
  {
    label: "Hackathon Judge",
    email: "judge@finsight.local",
    password: "JudgePassword2024!",
    role: "Auditor & Evaluator",
    icon: Sparkles,
    badge: "Recommended",
    badgeColor: "bg-indigo-500/20 text-indigo-300 border-indigo-500/30"
  },
  {
    label: "Salaried Professional",
    email: "arjun@techcorp.in",
    password: "ArjunSecure2024",
    role: "Full Tech Corp Account",
    icon: Briefcase,
    badge: "₹85k/mo",
    badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
  },
  {
    label: "Gig Economy Partner",
    email: "rahul@delivery.in",
    password: "RahulDelivery2024",
    role: "Zomato / Uber Partner",
    icon: Bike,
    badge: "Weekly",
    badgeColor: "bg-amber-500/20 text-amber-300 border-amber-500/30"
  },
  {
    label: "College Student",
    email: "ananya@university.edu",
    password: "StudentLife2024",
    role: "University Account",
    icon: GraduationCap,
    badge: "₹15k/mo",
    badgeColor: "bg-purple-500/20 text-purple-300 border-purple-500/30"
  }
];

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!email.trim() || !password) {
      setError("Please provide both email and password.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await statementApi.login(email.trim(), password);
      // Persist session locally
      localStorage.setItem('finsight_user', JSON.stringify(res.user));
      localStorage.setItem('finsight_token', res.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to authenticate session.");
    } finally {
      setLoading(false);
    }
  };

  const applyPreset = (preset) => {
    setEmail(preset.email);
    setPassword(preset.password);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#080d1a] flex flex-col justify-center items-center p-4 relative overflow-hidden">
      {/* Background Gradient Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-md w-full space-y-6 relative z-10">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 bg-gradient-to-tr from-indigo-600 to-indigo-400 rounded-2xl shadow-xl shadow-indigo-600/25 mb-1">
            <CreditCard className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center justify-center gap-2">
            FinSight <span className="text-xs uppercase px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">AI</span>
          </h1>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Bank Statement Intelligence & Financial Health Analyzer (PS-04)
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-5 backdrop-blur-md">
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-white">Sign In to Workspace</h2>
            <p className="text-xs text-slate-400">
              Access your local encrypted ledger analytics and Monte Carlo simulations.
            </p>
          </div>

          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Field */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 block">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@finsight.local"
                  required
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-300 block">
                  Password
                </label>
                <span className="text-[11px] text-indigo-400 hover:text-indigo-300 cursor-pointer">
                  Forgot key?
                </span>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl py-2.5 pl-10 pr-10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-3 text-slate-500 hover:text-slate-300 transition"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center justify-between text-xs pt-0.5">
              <label className="flex items-center gap-2 cursor-pointer text-slate-400 hover:text-slate-200">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-0 cursor-pointer"
                />
                <span>Remember this workstation</span>
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-2 transition shadow-lg shadow-indigo-600/30"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span>Authenticate Session</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Credentials (1-Click Fill) */}
          <div className="pt-3 border-t border-slate-800/80 space-y-2.5">
            <span className="text-[11px] font-bold uppercase text-slate-400 block tracking-wider">
              Instant Hackathon Demo Logins (1-Click Fill):
            </span>
            <div className="grid grid-cols-2 gap-2">
              {DEMO_PRESETS.map((preset) => {
                const Icon = preset.icon;
                const isSelected = email === preset.email;
                return (
                  <button
                    key={preset.email}
                    type="button"
                    onClick={() => applyPreset(preset)}
                    className={`p-2.5 rounded-xl border text-left transition space-y-1 ${
                      isSelected
                        ? 'bg-indigo-600/15 border-indigo-500/50 text-white'
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold text-white flex items-center gap-1.5">
                        <Icon className="w-3.5 h-3.5 text-indigo-400" />
                        {preset.label}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-400 block truncate">
                      {preset.email}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Zero-Telemetry Security Footer */}
        <div className="flex items-center justify-center gap-2 text-emerald-400 text-[11px] font-medium bg-emerald-500/5 border border-emerald-500/20 py-2.5 px-4 rounded-2xl">
          <ShieldCheck className="w-4 h-4 flex-shrink-0" />
          <span>Local SQLite Vault &bull; Zero Cloud Transmission &bull; PII Protected</span>
        </div>
      </div>
    </div>
  );
}
