import React, { useEffect, useRef } from 'react';
import { Shield, ArrowRight, Binary, Cpu, Sparkles } from 'lucide-react';
import { useProject } from '../../context/ProjectContext';
import { useNavigate } from 'react-router-dom';

export const ExecutiveHero: React.FC = () => {
  const { currentProject, setIsScanModalOpen } = useProject();
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = canvas.parentElement?.clientWidth || 800);
    let height = (canvas.height = 200);

    const particles: { x: number; y: number; vx: number; vy: number; radius: number; color: string }[] = [];
    const colors = ['#06B6D4', '#38BDF8', '#818CF8', '#10B981'];

    for (let i = 0; i < 28; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        radius: Math.random() * 2 + 1,
        color: colors[Math.floor(Math.random() * colors.length)],
      });
    }

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Draw faint connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 80) {
            ctx.strokeStyle = `rgba(6, 182, 212, ${0.15 * (1 - dist / 80)})`;
            ctx.lineWidth = 0.6;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }

      // Draw particles
      particles.forEach((p) => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.fill();

        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    const handleResize = () => {
      if (canvas && canvas.parentElement) {
        width = canvas.width = canvas.parentElement.clientWidth;
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-r from-[#0B0F19] via-[#0F172A] to-[#0B0F19] p-6 md:p-8 shadow-2xl mb-8">
      {/* Background Interactive Visual Canvas */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 pointer-events-none opacity-40 mix-blend-screen"
      />

      {/* Cyber Glow Accent */}
      <div className="absolute top-0 right-1/4 w-96 h-48 bg-cyan-500/10 blur-[100px] pointer-events-none" />

      <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        <div className="max-w-2xl space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-950/40 px-3 py-1 text-xs font-mono text-cyan-300">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>NIST Post-Quantum Cryptography (FIPS 203 / 204 / 205) Intelligence</span>
          </div>

          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white">
            Cryptographic Inventory & <br />
            <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-blue-400 bg-clip-text text-transparent">
              Post-Quantum Migration Architecture
            </span>
          </h1>

          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-xl">
            Continuous discovery, Mosca exposure modeling, and automated PQC upgrade simulation across code repositories, TLS sessions, and cryptographic dependencies.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              onClick={() => setIsScanModalOpen(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 px-5 py-2.5 text-xs font-bold text-slate-950 transition-all shadow-lg shadow-cyan-950/50 cursor-pointer hover:translate-y-[-1px]"
            >
              <span>Scan Source Code</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => navigate('/risk')}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900/80 hover:bg-slate-800 px-4 py-2.5 text-xs font-medium text-slate-200 transition-colors cursor-pointer"
            >
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>Simulate Mosca Risk</span>
            </button>

            <button
              onClick={() => navigate('/reports')}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-700/60 bg-slate-900/40 hover:bg-slate-800 px-4 py-2.5 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
            >
              <Binary className="w-4 h-4 text-slate-400" />
              <span>CycloneDX 1.6 CBOM</span>
            </button>
          </div>
        </div>

        {/* Status Callout Card */}
        <div className="shrink-0 w-full lg:w-72 rounded-xl border border-slate-800 bg-slate-900/70 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-xs text-slate-400 font-mono">
            <span>ACTIVE REPOSITORY</span>
            <span className="text-emerald-400 font-semibold">SYNCHRONIZED</span>
          </div>
          <div className="text-sm font-semibold text-slate-100 font-mono truncate mb-1">
            {currentProject?.name || 'No Project Selected'}
          </div>
          <div className="text-xs text-slate-400 mb-3 truncate">
            {currentProject?.description || 'Cryptographic inspection target'}
          </div>
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 bg-slate-950/60 p-2 rounded-lg border border-slate-800">
            <span>Quantum Horizon:</span>
            <span className="text-rose-400 font-semibold">2033 (Critical)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
