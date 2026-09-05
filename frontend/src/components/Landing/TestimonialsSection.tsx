import React from 'react';
import { motion } from 'framer-motion';
import { Quote } from 'lucide-react';

const testimonials = [
  {
    id: 1,
    initials: 'SK',
    name: 'Dr. Sarah Kim',
    title: 'CISO',
    company: 'FinTech Global',
    quote: 'SENTRIQ identified 47 quantum-vulnerable cryptographic implementations we had no visibility into. The Mosca theorem modeling gave our board the urgency data they needed to approve our PQC migration budget.',
    gradient: 'from-cyan-500 to-blue-600',
  },
  {
    id: 2,
    initials: 'RM',
    name: 'Raj Mehta',
    title: 'VP of Engineering',
    company: 'CloudSecure Inc.',
    quote: 'The automated PQC recommendation engine saved our team months of research. Going from RSA-2048 to ML-KEM-768 with sandbox simulation gave us confidence to deploy in production.',
    gradient: 'from-emerald-500 to-cyan-600',
  },
  {
    id: 3,
    initials: 'AL',
    name: 'Anna Liu',
    title: 'Head of Compliance',
    company: 'Gov Digital Services',
    quote: 'CycloneDX CBOM generation and the governance dashboard made our NIST compliance audit seamless. SENTRIQ is now a critical part of our security infrastructure.',
    gradient: 'from-purple-500 to-pink-600',
  }
];

export const TestimonialsSection: React.FC = () => {
  return (
    <section className="py-32 max-w-6xl mx-auto px-6 relative z-10">
      <div className="text-center mb-16">
        <h2 className="text-3xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-cyan-400 mb-6">
          Trusted by Security Leaders
        </h2>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto">
          What our enterprise clients say about SENTRIQ
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {testimonials.map((testimonial, index) => (
          <motion.div
            key={testimonial.id}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.15 }}
            className="bg-white/[0.03] backdrop-blur-md border border-white/[0.08] rounded-2xl p-8 hover:border-cyan-500/20 hover:-translate-y-[2px] transition-all duration-300 flex flex-col justify-between"
          >
            <div>
              <Quote className="text-cyan-500/30 mb-4 w-8 h-8" />
              <p className="text-slate-300 text-sm leading-relaxed italic">
                "{testimonial.quote}"
              </p>
            </div>
            
            <div className="flex items-center gap-3 mt-6">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white bg-gradient-to-br ${testimonial.gradient}`}>
                {testimonial.initials}
              </div>
              <div>
                <div className="text-white font-medium text-sm">{testimonial.name}</div>
                <div className="text-slate-500 text-xs">{testimonial.title}, {testimonial.company}</div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
};

export default TestimonialsSection;
