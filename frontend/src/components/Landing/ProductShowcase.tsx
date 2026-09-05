import React, { useState, useRef, useEffect } from 'react';
import { Search, AlertTriangle, ArrowRightLeft } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

type TabType = 'discovery' | 'risk' | 'migration';

export const ProductShowcase: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('discovery');
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (sectionRef.current) {
      gsap.fromTo(
        sectionRef.current,
        { opacity: 0, y: 30 },
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top 80%'
          }
        }
      );
    }
  }, []);

  return (
    <section id="product" ref={sectionRef} className="py-32 max-w-6xl mx-auto px-6">
      <div className="text-center mb-12">
        <h2 className="text-4xl font-bold bg-gradient-to-r from-white to-cyan-300 bg-clip-text text-transparent mb-4">
          See SENTRIQ in Action
        </h2>
        <p className="text-slate-400 text-lg">
          Interactive preview of our quantum migration intelligence platform
        </p>
      </div>

      <div className="flex flex-wrap justify-center gap-2 mb-8">
        <button
          onClick={() => setActiveTab('discovery')}
          className={`flex items-center gap-2 px-6 py-3 rounded-full font-medium transition-all duration-300 ${activeTab === 'discovery' ? 'bg-cyan-500/20 border border-cyan-500/50 text-cyan-300' : 'bg-white/[0.03] border border-white/[0.06] text-slate-400 hover:text-white'}`}
        >
          <Search className="w-4 h-4" /> Discovery
        </button>
        <button
          onClick={() => setActiveTab('risk')}
          className={`flex items-center gap-2 px-6 py-3 rounded-full font-medium transition-all duration-300 ${activeTab === 'risk' ? 'bg-cyan-500/20 border border-cyan-500/50 text-cyan-300' : 'bg-white/[0.03] border border-white/[0.06] text-slate-400 hover:text-white'}`}
        >
          <AlertTriangle className="w-4 h-4" /> Risk Analysis
        </button>
        <button
          onClick={() => setActiveTab('migration')}
          className={`flex items-center gap-2 px-6 py-3 rounded-full font-medium transition-all duration-300 ${activeTab === 'migration' ? 'bg-cyan-500/20 border border-cyan-500/50 text-cyan-300' : 'bg-white/[0.03] border border-white/[0.06] text-slate-400 hover:text-white'}`}
        >
          <ArrowRightLeft className="w-4 h-4" /> Migration
        </button>
      </div>

      <div className="bg-white/[0.02] backdrop-blur border border-white/[0.08] rounded-2xl p-8 min-h-[400px] overflow-hidden relative">
        <AnimatePresence mode="wait">
          {activeTab === 'discovery' && (
            <motion.div
              key="discovery"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              className="w-full h-full flex flex-col justify-center"
            >
              <h3 className="text-xl font-semibold text-white mb-6">Algorithm Distribution</h3>
              <div className="space-y-4">
                <div className="flex flex-col gap-2">
                  <div className="flex justify-between text-sm font-mono">
                    <span className="text-rose-400">RSA-2048 (VULNERABLE)</span>
                    <span className="text-slate-300">78%</span>
                  </div>
                  <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                    <motion.div initial={{ width: 0 }} animate={{ width: '78%' }} transition={{ duration: 1, delay: 0.1 }} className="h-full bg-rose-500" />
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  <div className="flex justify-between text-sm font-mono">
                    <span className="text-emerald-400">AES-256-GCM (SAFE)</span>
                    <span className="text-slate-300">15%</span>
                  </div>
                  <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                    <motion.div initial={{ width: 0 }} animate={{ width: '15%' }} transition={{ duration: 1, delay: 0.2 }} className="h-full bg-emerald-500" />
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  <div className="flex justify-between text-sm font-mono">
                    <span className="text-rose-400">ECDSA-P256 (VULNERABLE)</span>
                    <span className="text-slate-300">5%</span>
                  </div>
                  <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                    <motion.div initial={{ width: 0 }} animate={{ width: '5%' }} transition={{ duration: 1, delay: 0.3 }} className="h-full bg-rose-500" />
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  <div className="flex justify-between text-sm font-mono">
                    <span className="text-emerald-400">SHA-256 (SAFE)</span>
                    <span className="text-slate-300">2%</span>
                  </div>
                  <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                    <motion.div initial={{ width: 0 }} animate={{ width: '2%' }} transition={{ duration: 1, delay: 0.4 }} className="h-full bg-emerald-500" />
                  </div>
                </div>
              </div>
              <div className="mt-8 pt-4 border-t border-white/5 text-center text-slate-400 text-sm">
                636 cryptographic assets discovered across 2 repositories
              </div>
            </motion.div>
          )}

          {activeTab === 'risk' && (
            <motion.div
              key="risk"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              className="w-full h-full flex flex-col items-center justify-center"
            >
              <div className="text-center mb-8">
                <h3 className="text-xl font-semibold text-white mb-2">Mosca's Theorem Analysis</h3>
                <div className="text-2xl font-mono text-cyan-300 my-6 tracking-widest bg-cyan-950/30 p-4 rounded-xl border border-cyan-500/20 inline-block">
                  X + Y &gt; Z
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-3xl mb-10">
                <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-4 text-center">
                  <div className="text-slate-400 text-sm mb-1">Data Lifetime (X)</div>
                  <div className="text-3xl font-bold text-white">10<span className="text-lg text-slate-500 ml-1">yrs</span></div>
                </div>
                <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-4 text-center">
                  <div className="text-slate-400 text-sm mb-1">Migration Time (Y)</div>
                  <div className="text-3xl font-bold text-white">3<span className="text-lg text-slate-500 ml-1">yrs</span></div>
                </div>
                <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-4 text-center">
                  <div className="text-slate-400 text-sm mb-1">Threat Horizon (Z)</div>
                  <div className="text-3xl font-bold text-rose-400">2033</div>
                </div>
              </div>
              <div className="bg-rose-500/20 border border-rose-500/50 text-rose-200 px-6 py-3 rounded-full font-semibold flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-rose-400" />
                DEADLINE BREACH — Migrate by 2030
              </div>
            </motion.div>
          )}

          {activeTab === 'migration' && (
            <motion.div
              key="migration"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              className="w-full h-full flex flex-col justify-center"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex flex-col h-full">
                  <div className="text-sm font-medium text-rose-400 mb-3 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                    Before: RSA-2048 (Quantum Vulnerable)
                  </div>
                  <div className="bg-[#0B0F19] border border-rose-500/20 rounded-xl p-5 flex-1 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-rose-500/[0.02] pointer-events-none"></div>
                    <pre className="text-sm font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap">
                      <span className="text-purple-400">from</span> cryptography.hazmat.primitives.asymmetric <span className="text-purple-400">import</span> rsa{'\n'}
                      key = rsa.generate_private_key(65537, 2048)
                    </pre>
                  </div>
                </div>

                <div className="flex flex-col h-full">
                  <div className="text-sm font-medium text-emerald-400 mb-3 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                    After: ML-KEM-768 (FIPS 203)
                  </div>
                  <div className="bg-[#0B0F19] border border-emerald-500/20 rounded-xl p-5 flex-1 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-emerald-500/[0.02] pointer-events-none"></div>
                    <pre className="text-sm font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap">
                      <span className="text-purple-400">from</span> pqcrypto.kem <span className="text-purple-400">import</span> ml_kem_768{'\n'}
                      public_key, secret_key = ml_kem_768.keypair()
                    </pre>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
};

export default ProductShowcase;
