import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Compass,
  Search,
  ArrowRight,
  Sparkles,
  FolderGit2,
  ScanSearch,
  Binary,
  ShieldAlert,
  ShieldCheck,
  GitFork,
  FileSpreadsheet,
  Sliders,
  Layers,
  HelpCircle,
  RotateCcw,
  CheckCircle2,
  Terminal,
  ChevronRight,
  AlertTriangle,
} from 'lucide-react';
import { WhatsThisHelp } from '../components/Guide/WhatsThisHelp';

interface TopicItem {
  id: string;
  number?: string;
  title: string;
  category: 'GETTING_STARTED' | 'CONCEPTS' | 'REFERENCE';
  route?: string;
  icon: React.ComponentType<{ className?: string }>;
  what: string;
  why: string;
  next: string;
}

const TOPIC_ITEMS: TopicItem[] = [
  // GETTING STARTED (10)
  {
    id: 'projects',
    number: '01',
    title: 'Projects & Repositories',
    category: 'GETTING_STARTED',
    route: '/projects',
    icon: FolderGit2,
    what: 'Ingest Git repositories and assign data sensitivity labels, folder contexts, and default migration profiles.',
    why: 'Accurate repository configuration ensures QARS scoring reflects enterprise domain context.',
    next: 'Navigate to Projects, paste a repository URL or select an existing project.',
  },
  {
    id: 'scan',
    number: '02',
    title: 'Scan Orchestration',
    category: 'GETTING_STARTED',
    route: '/scan',
    icon: ScanSearch,
    what: 'Executes static analysis engines across AST source code, binary artifacts, certificates, and dependencies.',
    why: 'Discovers embedded keys, outdated libraries, and un-agile cryptographic implementations automatically.',
    next: 'Go to Scan Console and click "Start Scan" to populate the CBOM.',
  },
  {
    id: 'inventory',
    number: '03',
    title: 'Inventory & CBOM',
    category: 'GETTING_STARTED',
    route: '/inventory',
    icon: Binary,
    what: 'Complete Cryptographic Bill of Materials (CBOM) listing every detected primitive, key size, and location.',
    why: 'Provides mandatory visibility required for compliance reporting and risk assessment.',
    next: 'Filter inventory by "Needs Review" to classify unknown cryptographic primitives.',
  },
  {
    id: 'risk',
    number: '04',
    title: 'Risk & Mosca Theorem',
    category: 'GETTING_STARTED',
    route: '/risk',
    icon: ShieldAlert,
    what: 'Quantifies quantum exposure using Mosca\'s inequality: X (Shelf-Life) + Y (Migration Time) > Z (Threat Horizon).',
    why: 'Identifies Harvest-Now-Decrypt-Later (HNDL) exposure and deadline risk per asset.',
    next: 'Open Risk page and prioritize assets flagged as CRITICAL or DEADLINE RISK.',
  },
  {
    id: 'qars',
    number: '05',
    title: 'QARS Scoring',
    category: 'GETTING_STARTED',
    route: '/qars',
    icon: Binary,
    what: 'Quantum-Aware Risk Score: SENTRIQ\'s explainable 0–100 vulnerability score per asset.',
    why: 'Combines timeline pressure, algorithm risk, data sensitivity, and agility into an actionable metric.',
    next: 'Click any asset row on the QARS page to view "Why this score?" calculation details.',
  },
  {
    id: 'business-criticality',
    number: '06',
    title: 'Business Criticality',
    category: 'GETTING_STARTED',
    route: '/business-criticality',
    icon: Sliders,
    what: 'Configure domain baselines, asset criticality weights, and network exposure overrides.',
    why: 'Tailors risk calculations to your organization\'s regulatory and operational reality.',
    next: 'Adjust business criticality parameters for high-value applications.',
  },
  {
    id: 'recommendations',
    number: '07',
    title: 'PQC Recommendations',
    category: 'GETTING_STARTED',
    route: '/recommendations',
    icon: ShieldCheck,
    what: 'Rule-based mapping of classical algorithms (RSA, ECC) to NIST FIPS 203/204 candidate standards.',
    why: 'Provides standardized, low-risk replacement algorithms (e.g. ML-KEM-768, ML-DSA-65).',
    next: 'Review recommended PQC algorithms and select migration candidate.',
  },
  {
    id: 'migration',
    number: '08',
    title: 'Migration Lifecycle',
    category: 'GETTING_STARTED',
    route: '/migration',
    icon: GitFork,
    what: 'Transition plan generation, person-day effort calculation, and AST Sandbox Simulator.',
    why: 'Accelerates PQC refactoring while minimizing developer person-day cost.',
    next: 'Open Migration page and run Sandbox Simulator to preview refactored code diffs.',
  },
  {
    id: 'validation',
    number: '09',
    title: 'Validation & Regression',
    category: 'GETTING_STARTED',
    route: '/migration',
    icon: CheckCircle2,
    what: 'Automated test suite verifying post-quantum code changes preserve application correctness.',
    why: 'Guarantees refactored PQC implementations pass functional regression checks.',
    next: 'Execute automated regression validation on refactored AST modules.',
  },
  {
    id: 'reports',
    number: '10',
    title: 'Reports & CBOM Exports',
    category: 'GETTING_STARTED',
    route: '/reports',
    icon: FileSpreadsheet,
    what: 'Export CycloneDX 1.6 CBOM JSON, PDF Executive Summaries, and regulatory audit packages.',
    why: 'Demonstrates PQC compliance for board members, auditors, and government bodies.',
    next: 'Download PDF report or export CycloneDX 1.6 JSON.',
  },

  // CONCEPTS (8)
  {
    id: 'concept-cbom',
    title: 'CBOM (Cryptographic Bill of Materials)',
    category: 'CONCEPTS',
    icon: Binary,
    what: 'Structured inventory of all cryptographic assets, keys, certificates, and algorithms across an enterprise software stack.',
    why: 'Standardized format (CycloneDX 1.6) required by executive security mandates and PQC compliance regulations.',
    next: 'Explore the CBOM Viewer on the Reports page.',
  },
  {
    id: 'concept-pqc',
    title: 'PQC (Post-Quantum Cryptography)',
    category: 'CONCEPTS',
    icon: ShieldCheck,
    what: 'Cryptographic algorithms resistant to cryptanalysis by quantum computers (e.g. lattice-based ML-KEM, ML-DSA).',
    why: 'Replaces classical RSA, ECC, and Diffie-Hellman vulnerable to Shor\'s algorithm.',
    next: 'Inspect PQC algorithm mappings in the Recommendations catalog.',
  },
  {
    id: 'concept-shor',
    title: 'Shor\'s Algorithm',
    category: 'CONCEPTS',
    icon: Terminal,
    what: 'Quantum polynomial-time algorithm for integer factorization and discrete logarithms.',
    why: 'Completely breaks RSA, DSA, ECDSA, and ECDH when executed on a Cryptanalytically Relevant Quantum Computer (CRQC).',
    next: 'Check your vulnerable RSA/ECC asset exposure on the Risk page.',
  },
  {
    id: 'concept-grover',
    title: 'Grover\'s Algorithm',
    category: 'CONCEPTS',
    icon: Terminal,
    what: 'Quantum search algorithm providing quadratic speedup for unstructured search.',
    why: 'Halves effective bit security of symmetric ciphers (e.g. AES-128 becomes AES-64). AES-256 remains quantum-safe.',
    next: 'Ensure symmetric encryption algorithms use 256-bit key sizes.',
  },
  {
    id: 'concept-qars',
    title: 'QARS (Quantum-Aware Risk Score)',
    category: 'CONCEPTS',
    icon: Binary,
    what: 'Explainable 0–100 score combining timeline pressure (X, Y, Z), algorithm vulnerability, exposure rating, and agility.',
    why: 'Provides a single objective metric for prioritization across thousands of discovered primitives.',
    next: 'Review QARS scoring documentation and asset level breakdowns.',
  },
  {
    id: 'concept-mosca',
    title: 'Mosca Theorem',
    category: 'CONCEPTS',
    icon: ShieldAlert,
    what: 'Framework stating data is exposed if X (shelf-life) + Y (migration time) > Z (threat horizon).',
    why: 'Proves why Harvest-Now-Decrypt-Later (HNDL) attacks threaten long-lived sensitive data today.',
    next: 'Inspect Mosca status indicators across your scanned repositories.',
  },
  {
    id: 'concept-agility',
    title: 'Crypto Agility',
    category: 'CONCEPTS',
    icon: GitFork,
    what: 'Ability of an application to swap cryptographic algorithms with minimal code refactoring or architectural changes.',
    why: 'Modular crypto architectures drastically reduce migration time (Y) and overall risk.',
    next: 'Identify hardcoded primitives and refactor toward modular crypto wrappers.',
  },
  {
    id: 'concept-blast-radius',
    title: 'Blast Radius Analysis',
    category: 'CONCEPTS',
    icon: Layers,
    what: 'Call-graph analysis measuring how replacing a single cryptographic primitive impacts caller functions and services.',
    why: 'Prevents breaking downstream APIs when migrating core security algorithms.',
    next: 'View Dependency Impact graph on the Migration page.',
  },
];

interface GlossaryEntry {
  term: string;
  definition: string;
  category: string;
}

const GLOSSARY_ENTRIES: GlossaryEntry[] = [
  { term: 'CBOM', definition: 'Cryptographic Bill of Materials listing all algorithms, keys, and usage sites in CycloneDX 1.6 JSON.', category: 'Standard' },
  { term: 'PQC', definition: 'Post-Quantum Cryptography algorithms designed to withstand quantum computer cryptanalysis.', category: 'Cryptography' },
  { term: 'QARS', definition: 'Quantum-Aware Risk Score (0-100) evaluating timeline pressure, algorithm safety, and agility.', category: 'Scoring' },
  { term: 'Shor\'s Algorithm', definition: 'Quantum algorithm that efficiently factors integers and solves discrete logarithms, breaking RSA and ECC.', category: 'Quantum Physics' },
  { term: 'Grover\'s Algorithm', definition: 'Quantum search algorithm that halves symmetric encryption security margins.', category: 'Quantum Physics' },
  { term: 'Mosca Theorem', definition: 'Security inequality stating risk exists if X (data lifetime) + Y (migration time) > Z (threat horizon).', category: 'Risk Theorem' },
  { term: 'Crypto Agility', definition: 'Design pattern enabling seamless algorithm replacement without systemic application rewrites.', category: 'Architecture' },
  { term: 'Blast Radius', definition: 'Measure of code and API dependency spread affected by a cryptographic replacement.', category: 'Graph Science' },
  { term: 'Threat Scenario', definition: 'Specific quantum attack vector (e.g. Harvest-Now-Decrypt-Later, Signature Forgery).', category: 'Security' },
  { term: 'Migration Complexity', definition: 'Estimated effort rating (LOW, MEDIUM, HIGH) required to replace a primitive.', category: 'Lifecycle' },
  { term: 'Hybrid Cryptography', definition: 'Dual-mode mechanism combining classical (RSA/ECC) and PQC (ML-KEM) algorithms simultaneously.', category: 'Remediation' },
];

interface GuideProps {
  onStartTour?: () => void;
}

export const Guide: React.FC<GuideProps> = ({ onStartTour }) => {
  const [activeTab, setActiveTab] = useState<'GETTING_STARTED' | 'CONCEPTS' | 'REFERENCE'>('GETTING_STARTED');
  const [searchQuery, setSearchQuery] = useState('');
  const [openAccordion, setOpenAccordion] = useState<string | null>('projects');
  const navigate = useNavigate();

  const handleStartTourClick = () => {
    if (onStartTour) {
      onStartTour();
    } else {
      localStorage.setItem('sentriq_tour_current_step', '0');
      navigate('/projects');
    }
  };

  const handleRestartTourClick = () => {
    localStorage.removeItem('sentriq_tour_completed');
    localStorage.setItem('sentriq_tour_current_step', '0');
    if (onStartTour) {
      onStartTour();
    } else {
      navigate('/projects');
    }
  };

  const filteredTopics = TOPIC_ITEMS.filter((item) => {
    const matchesTab = item.category === activeTab;
    const matchesSearch =
      searchQuery === '' ||
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.what.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.why.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesTab && matchesSearch;
  });

  const filteredGlossary = GLOSSARY_ENTRIES.filter(
    (g) =>
      searchQuery === '' ||
      g.term.toLowerCase().includes(searchQuery.toLowerCase()) ||
      g.definition.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Pipeline Journey Steps (8 core steps matching routes)
  const journeyPipeline = [
    { label: 'Project', route: '/projects' },
    { label: 'Scan', route: '/scan' },
    { label: 'CBOM', route: '/inventory' },
    { label: 'Risk', route: '/risk' },
    { label: 'QARS', route: '/qars' },
    { label: 'Recommendation', route: '/recommendations' },
    { label: 'Migration & Validation', route: '/migration' },
    { label: 'Reports', route: '/reports' },
  ];

  return (
    <div className="space-y-8 pb-16 text-left">
      {/* Page Header */}
      <div className="rounded-3xl border border-slate-800 bg-[#06080F] p-6 md:p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold">
              <BookOpen className="w-4 h-4 text-cyan-400" />
              <span>SENTRIQ Documentation & User Guide</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold font-mono text-slate-100">
              Interactive Guide & PQC Methodologies
            </h1>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              Master cryptographic discovery, evaluate Mosca urgency, navigate NIST FIPS standards, and simulate post-quantum migration.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <button
              onClick={handleStartTourClick}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-700/80 font-mono text-xs font-bold transition-all shadow-lg hover:scale-105 cursor-pointer"
            >
              <Compass className="w-4 h-4 text-cyan-400 animate-spin-slow" />
              <span>Guide Me Through SENTRIQ</span>
            </button>

            <button
              onClick={handleRestartTourClick}
              className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-slate-200 font-mono text-xs font-medium transition-colors cursor-pointer"
              title="Restart Guided Tour"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Restart Tour</span>
            </button>
          </div>
        </div>

        {/* Guide Journey Visualization Pipeline */}
        <div className="mt-8 pt-6 border-t border-slate-800/80">
          <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
            <span>SENTRIQ END-TO-END TRANSITION JOURNEY</span>
            <WhatsThisHelp
              term="Guide Journey"
              title="What is the Transition Journey?"
              what="The 9-step methodology moving from repository ingestion to compliant PQC CBOM reporting."
              why="Ensures zero missed steps when auditing and migrating enterprise cryptography."
              next="Click any journey node to navigate directly."
            />
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none">
            {journeyPipeline.map((step, idx) => (
              <React.Fragment key={idx}>
                <button
                  onClick={() => navigate(step.route)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/80 hover:bg-cyan-950/60 border border-slate-800 hover:border-cyan-800/60 text-slate-300 hover:text-cyan-300 font-mono text-xs transition-all shrink-0 cursor-pointer"
                >
                  <span className="w-4 h-4 rounded-full bg-slate-800 text-[10px] text-slate-400 flex items-center justify-center font-bold">
                    {idx + 1}
                  </span>
                  <span>{step.label}</span>
                </button>
                {idx < journeyPipeline.length - 1 && (
                  <ChevronRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* Navigation Tabs & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        {/* Tabs */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('GETTING_STARTED')}
            className={`px-4 py-2 rounded-xl font-mono text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'GETTING_STARTED'
                ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-800/80'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            Getting Started (10)
          </button>

          <button
            onClick={() => setActiveTab('CONCEPTS')}
            className={`px-4 py-2 rounded-xl font-mono text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'CONCEPTS'
                ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-800/80'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            Core Concepts (8)
          </button>

          <button
            onClick={() => setActiveTab('REFERENCE')}
            className={`px-4 py-2 rounded-xl font-mono text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'REFERENCE'
                ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-800/80'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            Glossary & FAQ
          </button>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search guides or glossary..."
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-[#06080F] border border-slate-800 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
          />
        </div>
      </div>

      {/* Main Content Area */}
      {activeTab !== 'REFERENCE' ? (
        <div className="space-y-4">
          {filteredTopics.map((topic) => {
            const Icon = topic.icon;
            const isOpen = openAccordion === topic.id;

            return (
              <div
                key={topic.id}
                className={`rounded-2xl border transition-all ${
                  isOpen
                    ? 'border-cyan-800/80 bg-[#0B1120] shadow-xl'
                    : 'border-slate-800/80 bg-[#06080F] hover:border-slate-700'
                }`}
              >
                {/* Accordion Header */}
                <button
                  onClick={() => setOpenAccordion(isOpen ? null : topic.id)}
                  className="w-full p-5 flex items-center justify-between text-left cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    {topic.number && (
                      <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-950/80 px-2 py-1 rounded-lg border border-cyan-800/60">
                        {topic.number}
                      </span>
                    )}
                    <div className="p-2 rounded-xl bg-slate-900 text-cyan-300 border border-slate-800">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="font-mono font-bold text-slate-100 text-sm">
                        {topic.title}
                      </h3>
                      <p className="text-xs text-slate-400 line-clamp-1 mt-0.5 font-sans">
                        {topic.what}
                      </p>
                    </div>
                  </div>

                  <ChevronRight
                    className={`w-4 h-4 text-slate-400 transition-transform ${
                      isOpen ? 'rotate-90 text-cyan-400' : ''
                    }`}
                  />
                </button>

                {/* Accordion Body */}
                {isOpen && (
                  <div className="px-5 pb-5 pt-2 border-t border-slate-800/80 space-y-4 text-xs font-sans">
                    {/* WHAT */}
                    <div className="space-y-1 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-cyan-400">
                        WHAT IS IT?
                      </span>
                      <p className="text-slate-200 leading-relaxed">{topic.what}</p>
                    </div>

                    {/* WHY */}
                    <div className="space-y-1 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-400">
                        WHY DOES IT MATTER?
                      </span>
                      <p className="text-slate-200 leading-relaxed">{topic.why}</p>
                    </div>

                    {/* NEXT */}
                    <div className="space-y-2 bg-emerald-950/20 p-3.5 rounded-xl border border-emerald-900/40">
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-400">
                        WHAT SHOULD I DO NEXT?
                      </span>
                      <p className="text-emerald-200 leading-relaxed">{topic.next}</p>

                      {topic.route && (
                        <button
                          onClick={() => navigate(topic.route!)}
                          className="mt-2 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-900/60 hover:bg-emerald-900 text-emerald-300 border border-emerald-700/60 font-mono text-xs font-semibold transition-colors cursor-pointer"
                        >
                          <span>Open {topic.title} Route</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        /* REFERENCE TAB: SEARCHABLE GLOSSARY & FAQ */
        <div className="space-y-8 text-left">
          {/* Searchable Glossary Section */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-cyan-400" />
              <h3 className="font-mono font-bold text-slate-100 text-base">
                Searchable Cryptographic & PQC Glossary
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredGlossary.map((entry, idx) => (
                <div
                  key={idx}
                  className="rounded-2xl border border-slate-800/80 bg-[#06080F] p-4 space-y-2 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-mono font-bold text-cyan-300 text-sm">
                      {entry.term}
                    </h4>
                    <span className="px-2 py-0.5 rounded-full bg-slate-900 text-slate-400 font-mono text-[9px] border border-slate-800">
                      {entry.category}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans">
                    {entry.definition}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* FAQ Section */}
          <div className="space-y-4 pt-4 border-t border-slate-800">
            <div className="flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-amber-400" />
              <h3 className="font-mono font-bold text-slate-100 text-base">
                Frequently Asked Questions (FAQ)
              </h3>
            </div>

            <div className="space-y-3 font-sans text-xs">
              <div className="p-4 rounded-2xl bg-[#06080F] border border-slate-800 space-y-1">
                <h5 className="font-mono font-bold text-slate-200 text-xs">
                  Q: What is Harvest-Now-Decrypt-Later (HNDL)?
                </h5>
                <p className="text-slate-400 leading-relaxed">
                  Adversaries intercept and archive encrypted communications today. When cryptanalytically relevant quantum computers emerge, they will decrypt historical traffic retroactively.
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-[#06080F] border border-slate-800 space-y-1">
                <h5 className="font-mono font-bold text-slate-200 text-xs">
                  Q: Why are NIST FIPS 203/204/205 standards important?
                </h5>
                <p className="text-slate-400 leading-relaxed">
                  NIST officially released final FIPS post-quantum standards in August 2024. ML-KEM (FIPS 203) and ML-DSA (FIPS 204) are the primary global benchmarks replacing RSA and ECC.
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-[#06080F] border border-slate-800 space-y-1">
                <h5 className="font-mono font-bold text-slate-200 text-xs">
                  Q: Does SENTRIQ modify my source code automatically?
                </h5>
                <p className="text-slate-400 leading-relaxed">
                  SENTRIQ generates simulated AST refactoring diffs in the Sandbox. You can preview changes, review regression test results, and validate before applying to production branches.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Guide;
