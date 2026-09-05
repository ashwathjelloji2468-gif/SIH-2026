import React, { useEffect, useRef } from 'react';
import { Shield, Activity, Zap, FileCode, FlaskConical, BarChart3 } from 'lucide-react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const features = [
  {
    icon: Shield,
    title: 'Quantum Threat Discovery',
    description: 'Deep AST-level scanning identifies every cryptographic primitive, protocol, and key across your entire codebase with deterministic accuracy.'
  },
  {
    icon: Activity,
    title: 'Mosca Risk Intelligence',
    description: 'Real-time threat horizon modeling using Michele Mosca\'s theorem to quantify your quantum vulnerability timeline.'
  },
  {
    icon: Zap,
    title: 'PQC Migration Engine',
    description: 'Automated code transformation recommendations mapping deprecated primitives to NIST FIPS 203/204/205 standards.'
  },
  {
    icon: FileCode,
    title: 'CycloneDX CBOM',
    description: 'Generate compliance-grade Cryptographic Bill of Materials in CycloneDX 1.6 format for governance and audit.'
  },
  {
    icon: FlaskConical,
    title: 'Sandbox Simulator',
    description: 'Safely test migration transformations with side-by-side code diffs before committing to production changes.'
  },
  {
    icon: BarChart3,
    title: 'Governance Dashboard',
    description: 'Complete audit trail, telemetry, and compliance monitoring across your entire quantum migration journey.'
  }
];

export const FeaturesSection: React.FC = () => {
  const sectionRef = useRef<HTMLElement>(null);
  const cardsRef = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    if (sectionRef.current) {
      gsap.fromTo(
        cardsRef.current,
        { opacity: 0, y: 40 },
        {
          opacity: 1,
          y: 0,
          stagger: 0.1,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top 80%',
          }
        }
      );
    }
  }, []);

  return (
    <section id="features" ref={sectionRef} className="py-32 relative">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold bg-gradient-to-r from-white to-cyan-300 bg-clip-text text-transparent mb-4">
            Quantum-Safe Security Suite
          </h2>
          <p className="text-slate-400 text-lg">
            Enterprise tools for the post-quantum era
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                ref={(el) => { cardsRef.current[index] = el; }}
                className="bg-white/[0.03] backdrop-blur-md border border-white/[0.08] rounded-2xl p-8 hover:border-cyan-500/30 hover:-translate-y-1 hover:shadow-[0_0_20px_rgba(6,182,212,0.15)] transition-all duration-300 group"
              >
                <div className="bg-cyan-950/40 rounded-xl p-3 inline-block mb-4 group-hover:bg-cyan-900/50 transition-colors">
                  <Icon className="w-10 h-10 text-cyan-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mt-4 mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
