import React, { useEffect, useRef } from 'react';

interface CyberVisualProps {
  className?: string;
  splineSceneUrl?: string; // Optional Spline scene URL
}

export const CyberVisual: React.FC<CyberVisualProps> = ({ className = '', splineSceneUrl }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let width = (canvas.width = canvas.parentElement?.clientWidth || 900);
    let height = (canvas.height = canvas.parentElement?.clientHeight || 280);

    // Cryptographic node lattice
    const nodes: {
      x: number;
      y: number;
      vx: number;
      vy: number;
      radius: number;
      color: string;
      baseColor: string;
    }[] = [];

    const colors = ['#06B6D4', '#38BDF8', '#818CF8', '#22D3EE', '#10B981'];

    for (let i = 0; i < 36; i++) {
      const col = colors[Math.floor(Math.random() * colors.length)];
      nodes.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        radius: Math.random() * 1.8 + 1,
        color: col,
        baseColor: col,
      });
    }

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Draw cryptographic quantum entanglement links
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 95) {
            const alpha = 0.18 * (1 - dist / 95);
            ctx.strokeStyle = `rgba(6, 182, 212, ${alpha})`;
            ctx.lineWidth = 0.7;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.stroke();
          }
        }
      }

      // Draw quantum nodes
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = n.color;
        ctx.shadowColor = n.color;
        ctx.shadowBlur = 6;
        ctx.fill();
        ctx.shadowBlur = 0;

        n.x += n.vx;
        n.y += n.vy;

        if (n.x < 0 || n.x > width) n.vx *= -1;
        if (n.y < 0 || n.y > height) n.vy *= -1;
      }

      animationId = requestAnimationFrame(render);
    };

    render();

    const handleResize = () => {
      if (canvas && canvas.parentElement) {
        width = canvas.width = canvas.parentElement.clientWidth;
        height = canvas.height = canvas.parentElement.clientHeight;
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <div className={`relative overflow-hidden pointer-events-none select-none ${className}`}>
      {/* Optional Spline Embed (Lazy loaded if URL provided) */}
      {splineSceneUrl && (
        <iframe
          src={splineSceneUrl}
          title="Spline 3D Scene"
          loading="lazy"
          className="absolute inset-0 w-full h-full border-0 opacity-70 mix-blend-screen"
        />
      )}

      {/* High-Performance Resilient Cyber Lattice Canvas (Active fallback) */}
      <canvas
        ref={canvasRef}
        className="w-full h-full mix-blend-screen opacity-50"
      />
    </div>
  );
};
