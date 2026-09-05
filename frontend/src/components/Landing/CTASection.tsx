import React from 'react';
import { motion } from 'framer-motion';

export const CTASection: React.FC = () => {
  return (
    <section className="py-32 relative overflow-hidden">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        className="max-w-4xl mx-auto mx-6 lg:mx-auto"
      >
        <div className="bg-gradient-to-br from-cyan-950/40 via-[#0B0F19] to-blue-950/40 border border-cyan-500/20 rounded-3xl p-16 text-center relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-blue-500/5 rounded-full blur-3xl" />
          
          <div className="relative z-10">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Ready to Quantum-Proof Your Infrastructure?
            </h2>
            <p className="text-lg text-slate-400 mt-6 max-w-xl mx-auto">
              Start with a free cryptographic scan of your codebase. Discover vulnerabilities before quantum computers do.
            </p>
            
            <div className="flex flex-col sm:flex-row justify-center items-center gap-4 mt-10">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="w-full sm:w-auto bg-cyan-500 hover:bg-cyan-400 text-black font-semibold px-8 py-4 rounded-xl text-lg shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-colors"
              >
                Start Free Scan
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="w-full sm:w-auto border border-white/20 bg-white/[0.05] hover:bg-white/[0.1] text-white px-8 py-4 rounded-xl text-lg transition-colors"
              >
                Schedule Demo
              </motion.button>
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
};

export default CTASection;
