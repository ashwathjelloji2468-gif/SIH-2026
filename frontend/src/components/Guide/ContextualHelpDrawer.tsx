import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  HelpCircle,
  X,
  Compass,
  BookOpen,
  ArrowRight,
  ShieldCheck,
  Binary,
  ShieldAlert,
  GitFork,
  FileSpreadsheet,
  Layers,
  FolderGit2,
  ScanSearch,
  Sliders,
  Sparkles,
  ExternalLink,
} from 'lucide-react';

interface PageHelpContent {
  title: string;
  badge: string;
  icon: React.ComponentType<{ className?: string }>;
  what: string;
  why: string;
  next: string;
  nextRoute?: string;
  keyConcepts: { term: string; definition: string }[];
}

const pageHelpMap: Record<string, PageHelpContent> = {
  '/dashboard': {
    title: 'Executive Quantum Dashboard',
    badge: 'OVERVIEW',
    icon: Layers,
    what: 'Centralized posture view summarizing project risk scores, threat horizons, and migration readiness across all repositories.',
    why: 'Provides CISO and security leadership immediate visibility into post-quantum vulnerability and timeline urgency.',
    next: 'Select a repository from the top dropdown or click a high-risk item to start discovery.',
    nextRoute: '/inventory',
    keyConcepts: [
      { term: 'Security Score', definition: 'Aggregate rating from 0-100 reflecting cryptographic safety across active scans.' },
      { term: 'Threat Horizon', definition: 'Estimated arrival year (~2033) for cryptanalytically relevant quantum computers.' },
      { term: 'Migration Readiness', definition: 'Percentage of classical algorithms mapped to NIST-standardized PQC candidates.' },
    ],
  },
  '/projects': {
    title: 'Repository Ingestion & Context',
    badge: 'INGESTION',
    icon: FolderGit2,
    what: 'Manage target source repositories, GitHub connections, and application business context overrides.',
    why: 'Cryptographic context (e.g. data sensitivity and business criticality) directly shapes accurate QARS and risk prioritization.',
    next: 'Ingest a repository URL or select an existing project to trigger automated scanning.',
    nextRoute: '/scan',
    keyConcepts: [
      { term: 'Project Scope', definition: 'Logical grouping of codebases sharing security governance policies.' },
      { term: 'Folder Context', definition: 'Override sensitivity and asset criticality per directory path.' },
    ],
  },
  '/scan': {
    title: 'Scan Orchestrator & CBOM Generator',
    badge: 'DISCOVERY',
    icon: ScanSearch,
    what: 'Executes static analysis detectors across source code, binaries, certificates, and dependencies to discover cryptographic primitives.',
    why: 'Manual audit misses embedded keys, outdated libraries, and hardcoded algorithms.',
    next: 'Click "Start Scan" to generate an updated CBOM and refresh asset inventory.',
    nextRoute: '/inventory',
    keyConcepts: [
      { term: 'CBOM', definition: 'Cryptographic Bill of Materials detailing every algorithm, key length, and usage site.' },
      { term: 'AST Analysis', definition: 'Abstract Syntax Tree parser extracting API calls (e.g. RSA, AES, ECDH).' },
    ],
  },
  '/inventory': {
    title: 'Cryptographic Asset Inventory & CBOM',
    badge: 'INVENTORY',
    icon: Binary,
    what: 'Definitive registry of discovered cryptographic algorithms, public keys, certificates, and cipher suites.',
    why: 'You cannot protect or migrate cryptography you do not know exists.',
    next: 'Filter by "Needs Review" to verify unknown primitives or inspect evidence snippets.',
    nextRoute: '/risk',
    keyConcepts: [
      { term: 'Crypto Asset', definition: 'Instance of cryptographic primitive, key, or protocol detected in code.' },
      { term: 'Evidence Item', definition: 'Exact line number, code snippet, and confidence score supporting discovery.' },
      { term: 'Unknown Review', definition: 'Triage workflow to classify unrecognized cryptographic routines.' },
    ],
  },
  '/risk': {
    title: 'Mosca Theorem & Risk Exposure Engine',
    badge: 'RISK SCIENCE',
    icon: ShieldAlert,
    what: 'Evaluates quantum vulnerability using Mosca Theorem: X (Data Shelf-Life) + Y (Migration Time) > Z (Quantum Threat Horizon).',
    why: 'Determines which assets face Harvest-Now-Decrypt-Later (HNDL) risk today versus future deadline risk.',
    next: 'Identify CRITICAL and HIGH priority assets needing immediate PQC transition planning.',
    nextRoute: '/qars',
    keyConcepts: [
      { term: 'Mosca Inequality', definition: 'If X + Y > Z, data security will collapse before migration completes.' },
      { term: 'HNDL Threat', definition: 'Adversaries harvest encrypted traffic today to decrypt when quantum computers arrive.' },
      { term: 'Threat Scenarios', definition: 'Specific exposure vectors (e.g. Signature Forgery, Key Exchange Decryption).' },
    ],
  },
  '/qars': {
    title: 'Quantum-Aware Risk Score (QARS)',
    badge: 'SCORING',
    icon: Binary,
    what: 'SENTRIQ\'s explainable 0–100 score combining timeline pressure (X, Y, Z), algorithm vulnerability, exposure rating, and agility.',
    why: 'Eliminates guesswork by quantifying exact risk severity per cryptographic asset.',
    next: 'Click any asset row to open "Why this score?" breakdown of core inputs and adjustments.',
    nextRoute: '/recommendations',
    keyConcepts: [
      { term: 'Timeline Pressure', definition: 'Normalized urgency ratio derived from remaining quantum threat horizon Z.' },
      { term: 'Algorithm Risk', definition: 'AQR adjustment based on mathematical vulnerability to Shor\'s or Grover\'s algorithm.' },
      { term: 'Agility Penalty', definition: 'Additional score added when hardcoded algorithms prevent modular replacement.' },
    ],
  },
  '/recommendations': {
    title: 'PQC Recommendation Engine',
    badge: 'REMEDIATION',
    icon: ShieldCheck,
    what: 'Maps vulnerable classical algorithms (RSA, ECC) to official NIST FIPS 203/204/205 post-quantum standards.',
    why: 'Ensures standards-compliant replacement algorithms (e.g. ML-KEM, ML-DSA) with performance and security tradeoffs.',
    next: 'Review recommended algorithm candidate and select target migration profile.',
    nextRoute: '/migration',
    keyConcepts: [
      { term: 'ML-KEM (FIPS 203)', definition: 'Primary lattice-based Key Encapsulation Mechanism replacing RSA/ECDH.' },
      { term: 'ML-DSA (FIPS 204)', definition: 'Primary digital signature algorithm replacing RSA-PSS and ECDSA.' },
      { term: 'Hybrid Cryptography', definition: 'Dual-encapsulation combining classical and PQC algorithms for defense-in-depth.' },
    ],
  },
  '/migration': {
    title: 'Migration Lifecycle & Sandbox Simulator',
    badge: 'TRANSITION',
    icon: GitFork,
    what: 'Calculates transition effort, generates side-by-side refactoring AST diffs, and simulates migration impact.',
    why: 'Reduces migration person-days by automating code transformations and regression testing.',
    next: 'Create a migration plan or run the Sandbox Simulator to preview automated code changes.',
    nextRoute: '/reports',
    keyConcepts: [
      { term: 'Migration Plan', definition: 'Structured task sequence with person-day effort estimations.' },
      { term: 'AST Sandbox', definition: 'Simulated refactoring environment showing before/after code diffs.' },
      { term: 'Dependency Impact', definition: 'Blast radius analysis on caller functions and API endpoints.' },
    ],
  },
  '/reports': {
    title: 'CBOM Exports & Audit Compliance',
    badge: 'COMPLIANCE',
    icon: FileSpreadsheet,
    what: 'Export standardized CycloneDX 1.6 CBOM JSON, PDF Executive Summaries, and regulatory compliance reports.',
    why: 'Fulfills executive board reporting and federal compliance requirements (e.g. NSM-10, OMB M-23-02).',
    next: 'Export CycloneDX CBOM or download PDF summary for audit stakeholders.',
    nextRoute: '/dashboard',
    keyConcepts: [
      { term: 'CycloneDX 1.6', definition: 'Standardized OWASP specification for Cryptographic Bill of Materials.' },
      { term: 'Executive Report', definition: 'High-level executive summary tailored for non-technical stakeholders.' },
    ],
  },
  '/business-criticality': {
    title: 'Business Criticality & Exposure Overrides',
    badge: 'GOVERNANCE',
    icon: Sliders,
    what: 'Configure project domain, data sensitivity, and business criticality parameters.',
    why: 'Allows security teams to fine-tune risk scoring based on enterprise context.',
    next: 'Adjust business criticality level and save context overrides.',
    nextRoute: '/risk',
    keyConcepts: [
      { term: 'Business Criticality', definition: 'Rating (Low to Critical) measuring operational impact if compromised.' },
      { term: 'Exposure Level', definition: 'Network reachability (Internal, External, Public API).' },
    ],
  },
  '/settings': {
    title: 'System Telemetry & Audit Logs',
    badge: 'SYSTEM',
    icon: Sliders,
    what: 'View system health, database statistics, scanner rule versions, and immutable audit event logs.',
    why: 'Ensures governance transparency and operational reliability across the SENTRIQ platform.',
    next: 'Check system health and audit log trail.',
    nextRoute: '/guide',
    keyConcepts: [
      { term: 'Audit Event', definition: 'Immutable record of user actions, scans, and policy modifications.' },
      { term: 'Rule Version', definition: 'Installed PQC knowledge base ruleset identifier.' },
    ],
  },
  '/guide': {
    title: 'SENTRIQ Platform User Guide & Tour',
    badge: 'DOCUMENTATION',
    icon: BookOpen,
    what: 'Interactive documentation hub containing getting started guides, concept breakdowns, and searchable glossary.',
    why: 'Helps teams onboard quickly and understand post-quantum cryptography concepts.',
    next: 'Launch the interactive Guided Tour to walk through SENTRIQ end-to-end.',
    nextRoute: '/dashboard',
    keyConcepts: [
      { term: 'Guided Tour', definition: 'Interactive step-by-step walkthrough highlighting UI components.' },
      { term: 'Searchable Glossary', definition: 'Comprehensive index of PQC, QARS, and Mosca terminology.' },
    ],
  },
};

interface ContextualHelpDrawerProps {
  onStartTour?: () => void;
}

export const ContextualHelpDrawer: React.FC<ContextualHelpDrawerProps> = ({ onStartTour }) => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const currentPath = location.pathname;
  const helpContent = pageHelpMap[currentPath] || pageHelpMap['/dashboard'];
  const IconComponent = helpContent.icon;

  return (
    <>
      {/* Floating Bottom-Right Help Trigger Button */}
      <div className="fixed bottom-6 right-6 z-40">
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2 px-3.5 py-2 rounded-full bg-cyan-950/90 hover:bg-cyan-900 border border-cyan-500/50 text-cyan-300 font-mono text-xs font-semibold shadow-2xl backdrop-blur-md transition-all hover:scale-105 group cursor-pointer"
          title="Contextual Help & Guide"
          aria-label="Open Contextual Help"
        >
          <HelpCircle className="w-4 h-4 text-cyan-400 group-hover:rotate-12 transition-transform" />
          <span className="hidden sm:inline">Guide & Help</span>
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
        </button>
      </div>

      {/* Right-Side Slide-Over Drawer / Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-xs transition-opacity"
            onClick={() => setIsOpen(false)}
          />

          <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
            <div className="w-screen max-w-md bg-[#0B1120] border-l border-slate-800 shadow-2xl flex flex-col justify-between">
              
              {/* Drawer Header */}
              <div className="p-6 border-b border-slate-800/80 bg-[#06080F]/80 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-xl bg-cyan-950/80 border border-cyan-800/60 text-cyan-300">
                    <IconComponent className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-mono text-[9px] font-bold tracking-wider">
                      {helpContent.badge}
                    </span>
                    <h3 className="font-mono font-bold text-slate-100 text-sm mt-0.5">
                      {helpContent.title}
                    </h3>
                  </div>
                </div>

                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 rounded-xl border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-900 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Drawer Scrollable Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs text-slate-300">
                
                {/* WHAT */}
                <div className="space-y-1.5 rounded-2xl border border-slate-800/80 bg-slate-900/50 p-4">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-cyan-400" />
                    <span>WHAT IS THIS PAGE?</span>
                  </span>
                  <p className="text-slate-200 leading-relaxed font-sans">{helpContent.what}</p>
                </div>

                {/* WHY */}
                <div className="space-y-1.5 rounded-2xl border border-slate-800/80 bg-slate-900/50 p-4">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-400">
                    WHY DOES IT MATTER?
                  </span>
                  <p className="text-slate-200 leading-relaxed font-sans">{helpContent.why}</p>
                </div>

                {/* KEY CONCEPTS */}
                <div className="space-y-2.5">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                    KEY CONCEPTS ON THIS PAGE
                  </span>
                  <div className="space-y-2">
                    {helpContent.keyConcepts.map((item, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-[#06080F] border border-slate-800/60 space-y-0.5">
                        <div className="font-mono font-semibold text-cyan-300 text-xs">
                          {item.term}
                        </div>
                        <div className="text-slate-400 text-[11px] leading-relaxed">
                          {item.definition}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* WHAT SHOULD I DO NEXT */}
                <div className="space-y-2 rounded-2xl border border-emerald-950/70 bg-emerald-950/20 p-4">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-400">
                    WHAT SHOULD I DO NEXT?
                  </span>
                  <p className="text-emerald-200 leading-relaxed font-sans">{helpContent.next}</p>
                  
                  {helpContent.nextRoute && (
                    <button
                      onClick={() => {
                        setIsOpen(false);
                        navigate(helpContent.nextRoute!);
                      }}
                      className="mt-2 w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-emerald-900/60 hover:bg-emerald-900 text-emerald-300 border border-emerald-700/60 font-mono text-xs font-semibold transition-colors cursor-pointer"
                    >
                      <span>Take Action ({helpContent.nextRoute})</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  )}
                </div>

              </div>

              {/* Drawer Footer Actions */}
              <div className="p-5 border-t border-slate-800 bg-[#06080F] space-y-2.5">
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => {
                      setIsOpen(false);
                      if (onStartTour) onStartTour();
                    }}
                    className="flex items-center justify-center gap-1.5 p-2.5 rounded-xl bg-cyan-950 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 font-mono text-xs font-semibold transition-colors cursor-pointer"
                  >
                    <Compass className="w-3.5 h-3.5" />
                    <span>Start Tour</span>
                  </button>

                  <button
                    onClick={() => {
                      setIsOpen(false);
                      navigate('/guide');
                    }}
                    className="flex items-center justify-center gap-1.5 p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 font-mono text-xs font-semibold transition-colors cursor-pointer"
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>Full Guide</span>
                  </button>
                </div>

                <div className="text-center text-[10px] font-mono text-slate-500">
                  SENTRIQ PQC Knowledge Base • FIPS 203/204 Standardized
                </div>
              </div>

            </div>
          </div>
        </div>
      )}
    </>
  );
};
