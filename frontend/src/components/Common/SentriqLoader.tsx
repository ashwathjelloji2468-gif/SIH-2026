import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Sparkles } from 'lucide-react';
import { Sentriq3DLogo } from '../Three/Sentriq3DLogo';

interface SentriqLoaderProps {
  isLoading?: boolean;
  onFinish?: () => void;
  minDurationMs?: number;
}

const LOADING_STEPS = [
  'Initializing Quantum Intelligence Engine...',
  'Discovering Cryptographic Primitives & ASTs...',
  'Evaluating Mosca Threat Horizons...',
  'Establishing Post-Quantum Security Posture...',
];

export const SentriqLoader: React.FC<SentriqLoaderProps> = ({
  isLoading = true,
  onFinish,
  minDurationMs = 1400,
}) => {
  const [progress, setProgress] = useState<number>(0);
  const [stepIndex, setStepIndex] = useState<number>(0);
  const [visible, setVisible] = useState<boolean>(isLoading);

  useEffect(() => {
    if (!isLoading) {
      setProgress(100);
      const timer = setTimeout(() => {
        setVisible(false);
        if (onFinish) onFinish();
      }, 400);
      return () => clearTimeout(timer);
    }

    setVisible(true);
    setProgress(0);
    setStepIndex(0);

    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const pct = Math.min(Math.round((elapsed / minDurationMs) * 100), 98);
      setProgress(pct);

      if (pct < 30) setStepIndex(0);
      else if (pct < 60) setStepIndex(1);
      else if (pct < 85) setStepIndex(2);
      else setStepIndex(3);

      if (elapsed >= minDurationMs) {
        clearInterval(interval);
        setProgress(100);
        setTimeout(() => {
          setVisible(false);
          if (onFinish) onFinish();
        }, 350);
      }
    }, 40);

    return () => clearInterval(interval);
  }, [isLoading, minDurationMs, onFinish]);

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 0.98 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="fixed inset-0 z-[9999] bg-[#0B1120] flex flex-col items-center justify-center select-none overflow-hidden"
        >
          {/* Cyber Grid & Radial Glow Background */}
          <div className="absolute inset-0 bg-grid-cyber bg-hex-pattern opacity-15 pointer-events-none" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle,rgba(34,211,238,0.14)_0%,rgba(6,182,212,0.04)_45%,transparent_70%)] blur-3xl pointer-events-none" />

          {/* Centered Logo & Breathing Glow */}
          <div className="relative z-10 flex flex-col items-center text-center space-y-6">
            <motion.div
              animate={{
                scale: [0.97, 1.03, 0.97],
                filter: [
                  'drop-shadow(0 0 25px rgba(34, 211, 238, 0.25))',
                  'drop-shadow(0 0 45px rgba(34, 211, 238, 0.5))',
                  'drop-shadow(0 0 25px rgba(34, 211, 238, 0.25))',
                ],
              }}
              transition={{ duration: 2.8, repeat: Infinity, ease: 'easeInOut' }}
              className="flex items-center gap-4"
            >
              <Sentriq3DLogo size="lg" showText={false} interactive={false} />
            </motion.div>

            {/* Brand Title */}
            <div className="space-y-1">
              <h1 className="text-3xl sm:text-4xl font-extrabold font-mono tracking-widest bg-gradient-to-r from-white via-[#80F2FF] to-[#22D3EE] bg-clip-text text-transparent">
                SENTRIQ
              </h1>
              <div className="text-[11px] font-mono text-[#94A3B8] tracking-widest uppercase">
                Quantum Intelligence Platform
              </div>
            </div>

            {/* Progress Bar Container */}
            <div className="w-64 sm:w-80 space-y-3 pt-2">
              <div className="h-1.5 w-full rounded-full bg-[#1E293B] overflow-hidden border border-[#22D3EE]/20 p-0.5">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-[#00E5FF] to-[#22D3EE] shadow-[0_0_12px_rgba(34,211,238,0.8)]"
                  initial={{ width: '0%' }}
                  animate={{ width: `${progress}%` }}
                  transition={{ ease: 'easeOut', duration: 0.1 }}
                />
              </div>

              {/* Status Step Indicator */}
              <div className="h-5 flex items-center justify-center">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={stepIndex}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.25 }}
                    className="text-xs font-mono text-[#22D3EE] font-medium flex items-center gap-1.5 truncate max-w-xs"
                  >
                    <Sparkles className="w-3.5 h-3.5 animate-spin text-[#22D3EE]" />
                    <span>{LOADING_STEPS[stepIndex]}</span>
                  </motion.div>
                </AnimatePresence>
              </div>
            </div>

            {/* NIST Standard Compliance Badge */}
            <div className="pt-4">
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#1E293B]/80 border border-[#22D3EE]/30 text-[#94A3B8] text-[10px] font-mono font-semibold tracking-wider uppercase backdrop-blur-md">
                <span className="w-1.5 h-1.5 rounded-full bg-[#22D3EE] animate-ping" />
                NIST PQC FIPS 203 / 204 / 205 Ready
              </span>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
