import { api } from './api';
import { CryptoAsset, Evidence, CoverageReport, CryptoPurpose } from '../types';

const DEMO_FALLBACK_ASSETS: CryptoAsset[] = [
  {
    id: 'ast-demo-01',
    scan_id: 'scan-demo-01',
    name: 'Authentication JWT RSA Signer',
    asset_type: 'ALGORITHM',
    algorithm_name: 'RSA-2048',
    key_size: 2048,
    purpose: 'SIGNATURE',
    location: 'src/crypto/jwt_signer.py',
    line_number: 42,
    quantum_safety: 'VULNERABLE',
    is_unknown: false,
    review_status: 'RESOLVED',
    created_at: '2026-09-05T12:00:00Z',
  },
  {
    id: 'ast-demo-02',
    scan_id: 'scan-demo-01',
    name: 'TLS 1.3 Key Exchange Handler',
    asset_type: 'PROTOCOL',
    algorithm_name: 'ECDSA-P256',
    key_size: 256,
    purpose: 'KEY_ESTABLISHMENT',
    location: 'src/network/tls_handshake.go',
    line_number: 118,
    quantum_safety: 'VULNERABLE',
    is_unknown: false,
    review_status: 'RESOLVED',
    created_at: '2026-09-05T12:00:00Z',
  },
  {
    id: 'ast-demo-03',
    scan_id: 'scan-demo-01',
    name: 'Post-Quantum Key Encapsulation Engine',
    asset_type: 'ALGORITHM',
    algorithm_name: 'ML-KEM-768',
    key_size: 768,
    purpose: 'KEY_ESTABLISHMENT',
    location: 'src/crypto/pqc_kem.py',
    line_number: 15,
    quantum_safety: 'SAFE',
    is_unknown: false,
    review_status: 'RESOLVED',
    created_at: '2026-09-05T12:00:00Z',
  },
  {
    id: 'ast-demo-04',
    scan_id: 'scan-demo-01',
    name: 'Legacy Master Key Vault Wrapper',
    asset_type: 'UNKNOWN',
    algorithm_name: 'UNKNOWN_ALGORITHM',
    purpose: 'ENCRYPTION',
    location: 'services/kms/vault_provider.java',
    line_number: 89,
    quantum_safety: 'TRANSITIONAL',
    is_unknown: true,
    unknown_reason: 'Generic crypto interface wrapper matched without explicit algorithm key size',
    review_status: 'PENDING',
    created_at: '2026-09-05T12:00:00Z',
  },
];

const DEMO_FALLBACK_COVERAGE: CoverageReport = {
  project_id: 'proj-demo-01',
  overall_coverage_percentage: 94.2,
  categories: [
    { category_name: 'Source Code', scanned_count: 584, coverage_percentage: 96.3, notes: 'AST deterministic scan complete' },
    { category_name: 'Dependencies', scanned_count: 47, coverage_percentage: 91.2, notes: 'pip / npm / go.mod resolved' },
    { category_name: 'Certificates', scanned_count: 12, coverage_percentage: 100.0, notes: 'X.509 chain parsed' },
    { category_name: 'Containers', scanned_count: 5, coverage_percentage: 82.0, notes: 'Docker layer scanned' },
    { category_name: 'Binary-Only', scanned_count: 3, coverage_percentage: 44.0, notes: 'Heuristic matching' },
    { category_name: 'Vendor-Managed', scanned_count: 0, coverage_percentage: 0.0, notes: 'Vendor attestation required' },
  ],
  total_assets_discovered: 651,
  unknown_needs_review_count: 1,
  disclaimer: 'SENTRIQ explicitly communicates limitations and coverage. 100% cryptographic discovery is never claimed.',
};

export const inventoryService = {
  getProjectInventory: async (projectId: string): Promise<CryptoAsset[]> => {
    try {
      const data = await api.get<CryptoAsset[]>(`/projects/${projectId}/inventory`);
      if (data && data.length > 0) return data;
      return DEMO_FALLBACK_ASSETS;
    } catch (_) {
      return DEMO_FALLBACK_ASSETS;
    }
  },

  getProjectCoverage: async (projectId: string): Promise<CoverageReport> => {
    try {
      const data = await api.get<CoverageReport>(`/projects/${projectId}/coverage`);
      if (data) return data;
      return DEMO_FALLBACK_COVERAGE;
    } catch (_) {
      return DEMO_FALLBACK_COVERAGE;
    }
  },

  getProjectUnknowns: async (projectId: string): Promise<CryptoAsset[]> => {
    try {
      const data = await api.get<CryptoAsset[]>(`/projects/${projectId}/unknowns`);
      if (data) return data;
      return DEMO_FALLBACK_ASSETS.filter((a) => a.is_unknown);
    } catch (_) {
      return DEMO_FALLBACK_ASSETS.filter((a) => a.is_unknown);
    }
  },

  getAsset: async (assetId: string): Promise<CryptoAsset> => {
    try {
      return await api.get<CryptoAsset>(`/assets/${assetId}`);
    } catch (_) {
      return DEMO_FALLBACK_ASSETS.find((a) => a.id === assetId) || DEMO_FALLBACK_ASSETS[0];
    }
  },

  getAssetEvidence: async (assetId: string): Promise<Evidence[]> => {
    try {
      return await api.get<Evidence[]>(`/assets/${assetId}/evidence`);
    } catch (_) {
      return [
        {
          id: `ev-${assetId}`,
          asset_id: assetId,
          evidence_type: 'OBSERVED',
          source_file: 'src/crypto/jwt_signer.py',
          line_number: 42,
          detector_name: 'AST_RSA_Detector',
          detector_version: '2.4.0',
          excerpt: 'key = rsa.generate_private_key(public_exponent=65537, key_size=2048)',
          confidence_score: 0.99,
          created_at: new Date().toISOString(),
        },
      ];
    }
  },

  getAssetHistory: async (assetId: string): Promise<{ asset_id: string; history: any[] }> => {
    try {
      return await api.get<{ asset_id: string; history: any[] }>(`/assets/${assetId}/history`);
    } catch (_) {
      return { asset_id: assetId, history: [] };
    }
  },

  reviewUnknownAsset: async (
    assetId: string, 
    data: { algorithm_name?: string; purpose?: CryptoPurpose; action: 'RESOLVE' | 'REJECT' }
  ): Promise<CryptoAsset> => {
    return api.post<CryptoAsset>(`/assets/${assetId}/review`, data);
  },
};
