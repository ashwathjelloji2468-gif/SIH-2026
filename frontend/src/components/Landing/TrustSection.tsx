import React, { useEffect, useRef, useState } from 'react';
import { Shield, Lock, Award, FileCheck } from 'lucide-react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const StatNumber: React.FC<{ end: number; decimals?: number; suffix?: string; isVisible: boolean }> = ({ end, decimals = 0, suffix = '', isVisible }) => {
  const [value, setValue] = useState(0);

  useEffect(() => {
    if (!isVisible) return;
    
    let startTime: number | null = null;
    const duration = 2000;
    
    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime;
      const progress = Math.min((currentTime - startTime) / duration, 1);
      
      const easeProgress = 1 - Math.pow(1 - progress, 3); // cubic ease out
      setValue(end * easeProgress);
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    
    requestAnimationFrame(animate);
  }, [end, isVisible]);

  return (
    <span>
      {value.toFixed(decimals)}
      {suffix}
    </span>
  );
};

export const TrustSection: React.FC = () => {
  const sectionRef = useRef<HTMLElement>(null);
  const statsRef = useRef<HTMLDivElement>(null);
  const badgesRef = useRef<HTMLDivElement>(null);
  const [statsVisible, setStatsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setStatsVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.3 }
    );

    if (statsRef.current) {
      observer.observe(statsRef.current);
    }

    if (sectionRef.current && badgesRef.current) {
      gsap.fromTo(
        badgesRef.current.children,
        { opacity: 0, y: 30 },
        {
          opacity: 1,
          y: 0,
          stagger: 0.1,
          duration: 0.8,
          scrollTrigger: {
            trigger: badgesRef.current,
            start: 'top 85%'
          }
        }
      );
    }

    return () => observer.disconnect();
  }, []);

  const integrations = ['GitHub', 'GitLab', 'AWS', 'Azure', 'Docker', 'Kubernetes', 'Jenkins', 'Terraform'];

  return (
    <section id="security" ref={sectionRef} className="py-32 overflow-hidden">
      {/* Stats Counter Row */}
      <div ref={statsRef} className="max-w-4xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8 mb-20">
        <div className="text-center">
          <div className="text-4xl font-bold text-white mb-2">
            <StatNumber end={636} suffix="+" isVisible={statsVisible} />
          </div>
          <div className="text-sm text-slate-400">Crypto Assets Discovered</div>
        </div>
        <div className="text-center">
          <div className="text-4xl font-bold text-white mb-2">
            <StatNumber end={99.4} decimals={1} suffix="%" isVisible={statsVisible} />
          </div>
          <div className="text-sm text-slate-400">Detection Accuracy</div>
        </div>
        <div className="text-center">
          <div className="text-4xl font-bold text-white mb-2">
            <StatNumber end={5} isVisible={statsVisible} />
          </div>
          <div className="text-sm text-slate-400">Enterprise Deployments</div>
        </div>
        <div className="text-center">
          <div className="text-4xl font-bold text-white mb-2">
            FIPS 203/204/205
          </div>
          <div className="text-sm text-slate-400">NIST Compliant</div>
        </div>
      </div>

      {/* Security Badges Row */}
      <div ref={badgesRef} className="flex justify-center gap-6 flex-wrap px-6 max-w-5xl mx-auto">
        <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl px-6 py-4 flex items-center gap-3 hover:border-cyan-500/30 hover:shadow-[0_0_15px_rgba(6,182,212,0.15)] transition-all duration-300 cursor-default">
          <Shield className="w-6 h-6 text-cyan-400" />
          <span className="font-semibold text-white">ISO 27001</span>
        </div>
        <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl px-6 py-4 flex items-center gap-3 hover:border-cyan-500/30 hover:shadow-[0_0_15px_rgba(6,182,212,0.15)] transition-all duration-300 cursor-default">
          <Lock className="w-6 h-6 text-cyan-400" />
          <span className="font-semibold text-white">SOC 2 Type II</span>
        </div>
        <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl px-6 py-4 flex items-center gap-3 hover:border-cyan-500/30 hover:shadow-[0_0_15px_rgba(6,182,212,0.15)] transition-all duration-300 cursor-default">
          <Award className="w-6 h-6 text-cyan-400" />
          <span className="font-semibold text-white">NIST PQC</span>
        </div>
        <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl px-6 py-4 flex items-center gap-3 hover:border-cyan-500/30 hover:shadow-[0_0_15px_rgba(6,182,212,0.15)] transition-all duration-300 cursor-default">
          <FileCheck className="w-6 h-6 text-cyan-400" />
          <span className="font-semibold text-white">CycloneDX 1.6</span>
        </div>
      </div>

      {/* Logo Marquee */}
      <div className="mt-20 overflow-hidden w-full relative">
        <div className="absolute left-0 top-0 bottom-0 w-24 bg-gradient-to-r from-[#0B1120] to-transparent z-10 pointer-events-none"></div>
        <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-[#0B1120] to-transparent z-10 pointer-events-none"></div>
        
        <style>
          {`
            @keyframes marquee {
              from { transform: translateX(0); }
              to { transform: translateX(-50%); }
            }
          `}
        </style>
        
        <div 
          className="flex gap-4 w-max"
          style={{ animation: 'marquee 30s linear infinite' }}
        >
          {[...integrations, ...integrations, ...integrations].map((item, i) => (
            <div 
              key={i} 
              className="px-6 py-3 bg-white/[0.02] backdrop-blur-sm border border-white/[0.05] rounded-full text-slate-400 font-medium whitespace-nowrap"
            >
              {item}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default TrustSection;
