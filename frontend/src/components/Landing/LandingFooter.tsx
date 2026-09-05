import React from 'react';
import { Shield } from 'lucide-react';

export const LandingFooter: React.FC = () => {
  const footerLinks = [
    {
      title: 'Product',
      links: ['Dashboard', 'Scan Engine', 'Inventory', 'Risk Analysis', 'Migration']
    },
    {
      title: 'Resources',
      links: ['Documentation', 'API Reference', 'Blog', 'Changelog']
    },
    {
      title: 'Company',
      links: ['About', 'Careers', 'Contact', 'Partners']
    },
    {
      title: 'Legal',
      links: ['Privacy Policy', 'Terms of Service', 'Security', 'Compliance']
    }
  ];

  return (
    <footer className="relative border-t border-cyan-500/15 bg-[#0B1120]">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/2 h-px bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent" />
      
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {footerLinks.map((column, idx) => (
            <div key={idx}>
              <h3 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">
                {column.title}
              </h3>
              <ul className="space-y-2">
                {column.links.map((link, linkIdx) => (
                  <li key={linkIdx}>
                    <a href="#" className="text-sm text-slate-500 hover:text-cyan-400 transition-colors block py-1">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 pt-8 border-t border-white/[0.06] flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-white font-bold text-xl">
              <Shield className="w-6 h-6 text-cyan-500" />
              <span>SENTRIQ</span>
            </div>
            <span className="text-slate-500 text-sm hidden md:inline">|</span>
            <span className="text-slate-500 text-sm">
              © {new Date().getFullYear()} SENTRIQ. All rights reserved.
            </span>
          </div>
          
          <div className="text-cyan-500/80 text-sm font-medium">
            Powered by NIST PQC Standards
          </div>
        </div>
      </div>
    </footer>
  );
};

export default LandingFooter;
