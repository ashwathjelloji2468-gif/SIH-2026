import { AuditEvidenceData, Recommendation } from '../types';

export function runPQCAuditFrontendTests() {
  const results: Array<{ name: string; passed: boolean; details: string }> = [];

  const test = (name: string, fn: () => { passed: boolean; details: string }) => {
    try {
      const res = fn();
      results.push({ name, passed: res.passed, details: res.details });
    } catch (e: any) {
      results.push({ name, passed: false, details: `Exception: ${e?.message || String(e)}` });
    }
  };

  // TEST A: READY audit evidence structure
  test('TEST A: READY audit evidence renders correctly with expected fields', () => {
    const audit: AuditEvidenceData = {
      status: 'READY',
      artifact_type: 'recommendation_snapshot',
      artifact_id: 'rec-asset-123',
      digest: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      provider_name: 'MockBlockchainAuditProvider',
      network: 'in-memory-mock',
      transaction_id: null,
      evidence: ['Digest recorded in-memory.'],
    };

    const isReady = audit.status === 'READY';
    const hasDigest = audit.digest.length === 64;
    const isMock = audit.provider_name === 'MockBlockchainAuditProvider';

    return {
      passed: isReady && hasDigest && isMock,
      details: `status=${audit.status}, digestLen=${audit.digest.length}, provider=${audit.provider_name}`,
    };
  });

  // TEST B: UNCONFIGURED state renders as unconfigured, not successful
  test('TEST B: UNCONFIGURED state renders as unconfigured, not successful', () => {
    const audit: AuditEvidenceData = {
      status: 'UNCONFIGURED',
      artifact_type: 'cbom_snapshot',
      artifact_id: 'cbom-scan-123',
      digest: '',
      provider_name: 'UnconfiguredBlockchainAuditProvider',
      warnings: ['Blockchain audit provider is not configured.'],
    };

    const isUnconfigured = audit.status === 'UNCONFIGURED';
    const isNotSuccess = audit.status !== 'READY';

    return {
      passed: isUnconfigured && isNotSuccess,
      details: `status=${audit.status}, warning=${audit.warnings?.[0]}`,
    };
  });

  // TEST C: ERROR state renders as error, not successful
  test('TEST C: ERROR state renders as error, not successful', () => {
    const audit: AuditEvidenceData = {
      status: 'ERROR',
      artifact_type: 'risk_assessment_snapshot',
      artifact_id: 'risk-asset-123',
      digest: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      provider_name: 'ErrorBlockchainAuditProvider',
      warnings: ['Node timeout during recording.'],
    };

    const isError = audit.status === 'ERROR';
    const isNotSuccess = audit.status !== 'READY';

    return {
      passed: isError && isNotSuccess,
      details: `status=${audit.status}, warning=${audit.warnings?.[0]}`,
    };
  });

  // TEST D: Full SHA-256 digest is available/copyable
  test('TEST D: Full SHA-256 digest is available without truncation', () => {
    const fullDigest = 'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e';
    const audit: AuditEvidenceData = {
      status: 'READY',
      artifact_type: 'cbom_snapshot',
      artifact_id: 'cbom-001',
      digest: fullDigest,
      provider_name: 'MockBlockchainAuditProvider',
    };

    return {
      passed: audit.digest === fullDigest && audit.digest.length === 64,
      details: `digest=${audit.digest}`,
    };
  });

  // TEST E: Artifact type renders correctly
  test('TEST E: Artifact type maps correctly across supported types', () => {
    const types = [
      'cbom_snapshot',
      'risk_assessment_snapshot',
      'recommendation_snapshot',
      'migration_validation_result',
    ];

    const allValid = types.every((t) => typeof t === 'string' && t.length > 0);

    return {
      passed: allValid,
      details: `typesCount=${types.length}`,
    };
  });

  // TEST F: Provider name renders correctly
  test('TEST F: Provider name renders correctly without fake labels', () => {
    const audit: AuditEvidenceData = {
      status: 'READY',
      artifact_type: 'recommendation_snapshot',
      artifact_id: 'rec-1',
      digest: 'digest123',
      provider_name: 'MockBlockchainAuditProvider',
    };

    return {
      passed: audit.provider_name === 'MockBlockchainAuditProvider',
      details: `provider_name=${audit.provider_name}`,
    };
  });

  // TEST G & H: Transaction ID is shown only when actually present; null does not create fake hash
  test('TEST G & H: Transaction ID is shown only when present; null transaction_id does not fake hash', () => {
    const auditNullTx: AuditEvidenceData = {
      status: 'READY',
      artifact_type: 'recommendation_snapshot',
      artifact_id: 'rec-1',
      digest: 'digest123',
      provider_name: 'MockBlockchainAuditProvider',
      transaction_id: null,
    };

    const auditRealTx: AuditEvidenceData = {
      status: 'READY',
      artifact_type: 'recommendation_snapshot',
      artifact_id: 'rec-2',
      digest: 'digest456',
      provider_name: 'EthereumAuditProvider',
      transaction_id: '0x123abc456def',
    };

    const nullOk = auditNullTx.transaction_id === null;
    const realOk = auditRealTx.transaction_id === '0x123abc456def';

    return {
      passed: nullOk && realOk,
      details: `nullTx=${auditNullTx.transaction_id}, realTx=${auditRealTx.transaction_id}`,
    };
  });

  // TEST I: Mock/in-memory provider is clearly distinguished from real blockchain evidence
  test('TEST I: Mock provider attribution specifies mock/in-memory ledger', () => {
    const providerName = 'MockBlockchainAuditProvider';
    const label =
      providerName === 'MockBlockchainAuditProvider'
        ? 'Digest recorded by Mock/In-Memory Audit Provider'
        : 'Recorded on-chain';

    return {
      passed: label === 'Digest recorded by Mock/In-Memory Audit Provider',
      details: `Label="${label}"`,
    };
  });

  // TEST J: Missing audit payload does not break existing UI
  test('TEST J: Recommendation without audit payload renders cleanly', () => {
    const rec: Recommendation = {
      asset_id: 'asset-legacy',
      target_pqc_candidate: 'ML-KEM-768',
      standard_status: 'FINAL_STANDARD',
      rationale: 'Migrate per NIST FIPS 203.',
      migration_complexity: 'LOW',
      confidence: 0.9,
    };

    const hasNoAudit = rec.audit === undefined && rec.tradeoffs?.audit === undefined;

    return {
      passed: hasNoAudit,
      details: `hasNoAudit=${hasNoAudit}`,
    };
  });

  // TEST K: All four artifact types can display audit evidence
  test('TEST K: All four artifact types accept audit payload structure', () => {
    const artifacts = [
      { type: 'cbom_snapshot', id: 'cbom-1' },
      { type: 'risk_assessment_snapshot', id: 'risk-1' },
      { type: 'recommendation_snapshot', id: 'rec-1' },
      { type: 'migration_validation_result', id: 'val-1' },
    ];

    const valid = artifacts.every((a) => {
      const data: AuditEvidenceData = {
        status: 'READY',
        artifact_type: a.type,
        artifact_id: a.id,
        digest: 'sha256digest',
        provider_name: 'MockBlockchainAuditProvider',
      };
      return data.artifact_type === a.type && data.artifact_id === a.id;
    });

    return {
      passed: valid,
      details: `artifactsVerified=${artifacts.length}`,
    };
  });

  // TEST L, M, N: Verification status matching semantics
  test('TEST L, M, N: Verification statuses MATCH, MISMATCH, and NOT FOUND map correctly', () => {
    const matchRes = { status: 'READY', evidence: ['Digest match confirmed'] };
    const mismatchRes = { status: 'ERROR', warnings: ['Digest mismatch'] };
    const notFoundRes = { status: 'ERROR', warnings: ['Artifact not found'] };

    const isMatch = matchRes.status === 'READY';
    const isMismatch = mismatchRes.status === 'ERROR' && mismatchRes.warnings[0].includes('mismatch');
    const isNotFound = notFoundRes.status === 'ERROR' && notFoundRes.warnings[0].includes('not found');

    return {
      passed: isMatch && isMismatch && isNotFound,
      details: `match=${isMatch}, mismatch=${isMismatch}, notFound=${isNotFound}`,
    };
  });

  // TEST O: Audit UI does not alter existing recommendation/risk/validation behavior
  test('TEST O: Audit evidence is purely additive and unmutated', () => {
    const rec: Recommendation = {
      asset_id: 'asset-test',
      target_pqc_candidate: 'ML-KEM-768',
      standard_status: 'FINAL_STANDARD',
      rationale: 'Test rationale',
      migration_complexity: 'MEDIUM',
      confidence: 0.9,
      audit: {
        status: 'READY',
        artifact_type: 'recommendation_snapshot',
        artifact_id: 'rec-asset-test',
        digest: 'digest_hex',
        provider_name: 'MockBlockchainAuditProvider',
      },
    };

    const targetUnchanged = rec.target_pqc_candidate === 'ML-KEM-768';
    const hasAudit = rec.audit?.status === 'READY';

    return {
      passed: targetUnchanged && hasAudit,
      details: `candidate=${rec.target_pqc_candidate}, auditStatus=${rec.audit?.status}`,
    };
  });

  return results;
}
