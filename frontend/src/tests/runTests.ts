import { runActiveScanTrackerTests } from './scanStatusTracker.test';

console.log('=== RUNNING FRONTEND ACTIVE SCAN ISOLATION TESTS ===');
const results = runActiveScanTrackerTests();
let passed = 0;
let failed = 0;

results.forEach((res) => {
  if (res.passed) {
    passed++;
    console.log(`✓ [PASS] ${res.name} (${res.details})`);
  } else {
    failed++;
    console.log(`✗ [FAIL] ${res.name} (${res.details})`);
  }
});

console.log(`\nSummary: ${passed} passed, ${failed} failed out of ${results.length} tests.`);
