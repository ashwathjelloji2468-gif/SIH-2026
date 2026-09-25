// @ts-ignore
if (typeof import.meta.env === 'undefined') {
  // @ts-ignore
  import.meta.env = { VITE_API_URL: 'http://localhost:8000/api/v1' };
}

import { runActiveScanTrackerTests } from './scanStatusTracker.test';
import { runPollingLabelTests } from './pollingLabel.test';
import { runRegressionTimeoutTests } from './regressionTimeout.test';
import { runCBOMDiffTelemetryTests } from './cbomDiffTelemetry.test';
import { runNetworkNodes3DTests } from './networkNodes3D.test';
import { runQARSFrontendTests } from './qarsFrontend.test';
import { runPhase2PerformanceTests } from './phase2Performance.test';
import { runGuideFrontendTests } from './guideFrontend.test';
import { runPQCPerformanceFrontendTests } from './pqcPerformanceFrontend.test';
import { runPQCAuditFrontendTests } from './pqcAuditFrontend.test';

console.log('=== RUNNING FRONTEND ACTIVE SCAN, POLLING LABEL, QARS, PERF PHASE 2, GUIDE, 3D MESH, PQC PERF MODEL & AUDIT EVIDENCE TESTS ===');

async function main() {
  const activeScanResults = runActiveScanTrackerTests();
  const pollingLabelResults = runPollingLabelTests();
  const regressionTimeoutResults = runRegressionTimeoutTests();
  const cbomTelemetryResults = runCBOMDiffTelemetryTests();
  const networkNodes3DResults = runNetworkNodes3DTests();
  const qarsResults = runQARSFrontendTests();
  const guideResults = runGuideFrontendTests();
  const pqcPerfResults = runPQCPerformanceFrontendTests();
  const pqcAuditResults = runPQCAuditFrontendTests();
  const phase2PerfResults = await runPhase2PerformanceTests();

  const allResults = [
    ...activeScanResults,
    ...pollingLabelResults,
    ...regressionTimeoutResults,
    ...cbomTelemetryResults,
    ...networkNodes3DResults,
    ...qarsResults,
    ...guideResults,
    ...pqcPerfResults,
    ...pqcAuditResults,
    ...phase2PerfResults,
  ];
  let passed = 0;
  let failed = 0;

  allResults.forEach((res) => {
    if (res.passed) {
      passed++;
      console.log(`✓ [PASS] ${res.name} (${res.details})`);
    } else {
      failed++;
      console.log(`✗ [FAIL] ${res.name} (${res.details})`);
    }
  });

  console.log(`\nSummary: ${passed} passed, ${failed} failed out of ${allResults.length} frontend tests.`);
  const proc = (globalThis as any).process;
  if (failed > 0 && proc && typeof proc.exit === 'function') {
    proc.exit(1);
  }
}

main().catch((err) => {
  console.error('Test execution failed:', err);
  const proc = (globalThis as any).process;
  if (proc && typeof proc.exit === 'function') {
    proc.exit(1);
  }
});
