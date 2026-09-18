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

console.log('=== RUNNING FRONTEND ACTIVE SCAN, POLLING LABEL, REGRESSION TIMEOUT, CBOM TELEMETRY & 3D MESH TESTS ===');

const activeScanResults = runActiveScanTrackerTests();
const pollingLabelResults = runPollingLabelTests();
const regressionTimeoutResults = runRegressionTimeoutTests();
const cbomTelemetryResults = runCBOMDiffTelemetryTests();
const networkNodes3DResults = runNetworkNodes3DTests();

const allResults = [...activeScanResults, ...pollingLabelResults, ...regressionTimeoutResults, ...cbomTelemetryResults, ...networkNodes3DResults];
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
