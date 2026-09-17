import { runActiveScanTrackerTests } from './scanStatusTracker.test';
import { runPollingLabelTests } from './pollingLabel.test';

console.log('=== RUNNING FRONTEND ACTIVE SCAN & POLLING LABEL TESTS ===');

const activeScanResults = runActiveScanTrackerTests();
const pollingLabelResults = runPollingLabelTests();

const allResults = [...activeScanResults, ...pollingLabelResults];
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
