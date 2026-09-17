import { evaluateActiveScanTracker } from '../utils/scanStatusTracker';
import { Scan } from '../types';

function createMockScan(id: string, status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'): Scan {
  return {
    id,
    project_id: 'test-proj',
    status,
    target_path: '/test/path',
    scan_type: 'source',
    created_at: new Date().toISOString(),
    completed_at: status === 'RUNNING' || status === 'QUEUED' ? undefined : new Date().toISOString(),
    error_message: status === 'FAILED' ? 'Scan failed' : undefined,
    cbom_version: '1.6',
    scanner_rule_version: '2026.1.0',
  };
}

export function runActiveScanTrackerTests(): { name: string; passed: boolean; details: string }[] {
  const results: { name: string; passed: boolean; details: string }[] = [];

  // TEST 1: Active scan ID = A, A.status = RUNNING, another historical scan B.status = RUNNING -> UI shows RUNNING for A
  const scanA_Running = createMockScan('A', 'RUNNING');
  const scanB_Running = createMockScan('B', 'RUNNING');
  const res1 = evaluateActiveScanTracker([scanA_Running, scanB_Running], 'A');
  const test1Passed = res1.activeStatus === 'RUNNING' && res1.shouldShowActiveRunning === true && res1.isPollingActive === true;
  results.push({
    name: 'TEST 1: Active scan A RUNNING with historical B RUNNING -> UI shows RUNNING for A',
    passed: test1Passed,
    details: `activeStatus=${res1.activeStatus}, showRunning=${res1.shouldShowActiveRunning}, polling=${res1.isPollingActive}`,
  });

  // TEST 2: Active scan ID = A, A.status = COMPLETED, historical scan B.status = RUNNING -> UI shows COMPLETED, NOT RUNNING
  const scanA_Completed = createMockScan('A', 'COMPLETED');
  const res2 = evaluateActiveScanTracker([scanA_Completed, scanB_Running], 'A');
  const test2Passed = res2.activeStatus === 'COMPLETED' && res2.shouldShowActiveRunning === false && res2.isPollingActive === false;
  results.push({
    name: 'TEST 2: Active scan A COMPLETED with historical B RUNNING -> UI shows COMPLETED, NOT RUNNING',
    passed: test2Passed,
    details: `activeStatus=${res2.activeStatus}, showRunning=${res2.shouldShowActiveRunning}, polling=${res2.isPollingActive}`,
  });

  // TEST 3: Active scan ID = A, A.status = FAILED, historical scan B.status = RUNNING -> UI shows FAILED
  const scanA_Failed = createMockScan('A', 'FAILED');
  const res3 = evaluateActiveScanTracker([scanA_Failed, scanB_Running], 'A');
  const test3Passed = res3.activeStatus === 'FAILED' && res3.shouldShowActiveRunning === false && res3.isPollingActive === false;
  results.push({
    name: 'TEST 3: Active scan A FAILED with historical B RUNNING -> UI shows FAILED',
    passed: test3Passed,
    details: `activeStatus=${res3.activeStatus}, showRunning=${res3.shouldShowActiveRunning}, polling=${res3.isPollingActive}`,
  });

  // TEST 4: Active scan ID = A, A.status = CANCELLED, historical scan B.status = RUNNING -> UI shows CANCELLED
  const scanA_Cancelled = createMockScan('A', 'CANCELLED');
  const res4 = evaluateActiveScanTracker([scanA_Cancelled, scanB_Running], 'A');
  const test4Passed = res4.activeStatus === 'CANCELLED' && res4.shouldShowActiveRunning === false && res4.isPollingActive === false;
  results.push({
    name: 'TEST 4: Active scan A CANCELLED with historical B RUNNING -> UI shows CANCELLED',
    passed: test4Passed,
    details: `activeStatus=${res4.activeStatus}, showRunning=${res4.shouldShowActiveRunning}, polling=${res4.isPollingActive}`,
  });

  // TEST 5: No active scan ID, historical scan B.status = RUNNING -> UI does NOT show active RUNNING state
  const res5 = evaluateActiveScanTracker([scanB_Running], null);
  const test5Passed = res5.activeScan === null && res5.shouldShowActiveRunning === false && res5.isPollingActive === false;
  results.push({
    name: 'TEST 5: No active scan ID with historical B RUNNING -> UI does NOT show active RUNNING state',
    passed: test5Passed,
    details: `activeScan=${res5.activeScan}, showRunning=${res5.shouldShowActiveRunning}, polling=${res5.isPollingActive}`,
  });

  // TEST 6: Polling stops when active scan reaches COMPLETED
  const res6 = evaluateActiveScanTracker([scanA_Completed], 'A');
  const test6Passed = res6.isPollingActive === false;
  results.push({
    name: 'TEST 6: Polling stops when active scan reaches COMPLETED',
    passed: test6Passed,
    details: `isPollingActive=${res6.isPollingActive}`,
  });

  return results;
}
