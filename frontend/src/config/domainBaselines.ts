import { DomainBaseline } from '../types/xEngine';

export const DEFAULT_X_FALLBACK_YEARS = 20;

export const DOMAIN_BASELINES_LIST: DomainBaseline[] = [
  {
    key: 'banking_finance',
    title: 'Banking & Finance',
    baseline_x_years: 15,
    description: 'Financial records, transaction logs, payment credentials, and banking data.',
    compliance_references: ['PCI-DSS', 'GLBA', 'SOX'],
    keywords: ['bank', 'banking', 'finance', 'payment', 'ledger', 'pci']
  },
  {
    key: 'government_defense',
    title: 'Government & Defense',
    baseline_x_years: 50,
    description: 'Classified records, defense communication, intelligence, and state security archives.',
    compliance_references: ['FedRAMP', 'DISA STIG', 'NIST SP 800-53'],
    keywords: ['gov', 'government', 'defense', 'military', 'classified', 'intelligence']
  },
  {
    key: 'healthcare',
    title: 'Healthcare & Life Sciences',
    baseline_x_years: 30,
    description: 'Electronic health records (EHR), genomic data, medical device data, and patient history.',
    compliance_references: ['HIPAA', 'HITECH', 'GDPR Art 9'],
    keywords: ['health', 'healthcare', 'medical', 'patient', 'ehr', 'hipaa']
  },
  {
    key: 'telecom',
    title: 'Telecommunications',
    baseline_x_years: 10,
    description: 'Call detail records (CDR), network routing tables, subscriber telemetry, and signaling data.',
    compliance_references: ['FCC', 'ePrivacy', 'CISA'],
    keywords: ['telecom', '5g', 'lte', 'carrier', 'cdr', 'voip']
  },
  {
    key: 'energy_utilities',
    title: 'Energy & Critical Utilities',
    baseline_x_years: 20,
    description: 'Grid infrastructure telemetry, SCADA systems, smart meter data, and utility controls.',
    compliance_references: ['NERC CIP', 'IEC 62443'],
    keywords: ['energy', 'utility', 'grid', 'scada', 'smart_meter']
  },
  {
    key: 'aviation_transportation',
    title: 'Aviation & Transportation',
    baseline_x_years: 20,
    description: 'Avionics telemetry, flight navigation, maritime routing, and logistics management.',
    compliance_references: ['ICAO', 'FAA DO-178C', 'TSA'],
    keywords: ['aviation', 'flight', 'avionics', 'maritime', 'shipping']
  },
  {
    key: 'cloud_saas',
    title: 'Cloud & SaaS Infrastructure',
    baseline_x_years: 10,
    description: 'Tenant data, identity provider tokens, API gateways, and cloud service backbones.',
    compliance_references: ['SOC 2 Type II', 'ISO 27001', 'CSA STAR'],
    keywords: ['cloud', 'saas', 'tenant', 'identity', 'oauth', 'k8s']
  },
  {
    key: 'iot_embedded',
    title: 'IoT & Embedded Devices',
    baseline_x_years: 20,
    description: 'Firmware signatures, edge node telemetry, automotive ECUs, and smart home hubs.',
    compliance_references: ['ETSI EN 303 645', 'NIST IR 8259'],
    keywords: ['iot', 'embedded', 'firmware', 'microcontroller', 'automotive']
  },
  {
    key: 'legal_pharma',
    title: 'Legal & Pharmaceuticals',
    baseline_x_years: 30,
    description: 'Patents, intellectual property, clinical trials, contract archives, and legal discovery.',
    compliance_references: ['FDA 21 CFR Part 11', 'USPTO', 'EMA'],
    keywords: ['legal', 'patent', 'ip', 'pharma', 'clinical_trial']
  },
  {
    key: 'software_supply_chain',
    title: 'Software Supply Chain & DevSecOps',
    baseline_x_years: 10,
    description: 'Build pipelines, package repositories, code signing keys, and artifact stores.',
    compliance_references: ['SLSA Level 4', 'NIST SSDF'],
    keywords: ['supply_chain', 'pipeline', 'ci_cd', 'npm', 'pypi', 'build']
  },
  {
    key: 'media_social',
    title: 'Media Streaming & Social Media',
    baseline_x_years: 7,
    description: 'Content distribution DRM, user interaction logs, media feeds, and messaging metadata.',
    compliance_references: ['COPPA', 'GDPR', 'CCPA'],
    keywords: ['media', 'streaming', 'video', 'social', 'chat', 'drm']
  }
];

export function getDomainBaselineByKey(key: string): DomainBaseline | undefined {
  return DOMAIN_BASELINES_LIST.find(d => d.key === key);
}
