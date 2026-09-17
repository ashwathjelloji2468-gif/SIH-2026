import { computeIsLivePollingActive } from '../utils/scanStatusTracker';
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

export function runPollingLabelTests(): { name: string; passed: boolean; details: string }[] {
  const results: { name: string; passed: boolean; details: string }[] = [];

  const scanA_Running = createMockScan('A', 'RUNNING');
  const scanA_Completed = createMockScan('A', 'COMPLETED');
  const scanA_Failed = createMockScan('A', 'FAILED');
  const scanB_Running = createMockScan('B', 'RUNNING');

  // TEST 10: activeScanId = null -> "Live Polling Active" not rendered.
  const label10 = computeIsLivePollingActive([scanA_Running], null);
  results.push({
    name: 'TEST 10: activeScanId = null -> "Live Polling Active" not rendered',
    passed: label10 === false,
    details: `isLivePollingActive=${label10}`,
  });

  // TEST 11: activeScanId = running active scan -> label rendered.
  const label11 = computeIsLivePollingActive([scanA_Running], 'A');
  results.push({
    name: 'TEST 11: activeScanId = running active scan -> label rendered',
    passed: label11 === true,
    details: `isLivePollingActive=${label11}`,
  });

  // TEST 12: activeScanId = completed -> label not rendered.
  const label12 = computeIsLivePollingActive([scanA_Completed], 'A');
  results.push({
    name: 'TEST 12: activeScanId = completed -> label not rendered',
    passed: label12 === false,
    details: `isLivePollingActive=${label12}`,
  });

  // TEST 13: activeScanId = failed -> label not rendered.
  const label13 = computeIsLivePollingActive([scanA_Failed], 'A');
  results.push({
    name: 'TEST 13: activeScanId = failed -> label not rendered',
    passed: label13 === false,
    details: `isLivePollingActive=${label13}`,
  });

  // TEST 14: historical RUNNING scan exists but activeScanId = null -> label not rendered.
  const label14 = computeIsLivePollingActive([scanB_Running], null);
  results.push({
    name: 'TEST 14: historical RUNNING scan exists but activeScanId = null -> label not rendered',
    passed: label14 === false,
    details: `isLivePollingActive=${label14}`,
  });

  return results;
}
