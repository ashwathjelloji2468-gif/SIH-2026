import { Scan, ScanStatus } from '../types';

export interface ActiveScanTrackerResult {
  activeScan: Scan | null;
  activeStatus: ScanStatus | null;
  isPollingActive: boolean;
  shouldShowActiveRunning: boolean;
}

export function evaluateActiveScanTracker(
  scans: Scan[],
  activeScanId: string | null
): ActiveScanTrackerResult {
  if (!activeScanId) {
    return {
      activeScan: null,
      activeStatus: null,
      isPollingActive: false,
      shouldShowActiveRunning: false,
    };
  }

  const activeScan = scans.find((s) => s.id === activeScanId) || null;
  const activeStatus: ScanStatus = activeScan ? activeScan.status : 'RUNNING';

  const isTerminal = activeScan
    ? ['COMPLETED', 'FAILED', 'CANCELLED'].includes(activeScan.status)
    : false;

  const isPollingActive = !isTerminal;
  const shouldShowActiveRunning = activeStatus === 'RUNNING' || activeStatus === 'QUEUED';

  return {
    activeScan,
    activeStatus,
    isPollingActive,
    shouldShowActiveRunning,
  };
}

export function computeIsLivePollingActive(
  scans: Scan[],
  activeScanId: string | null
): boolean {
  if (!activeScanId) return false;
  const activeScan = scans.find((s) => s.id === activeScanId);
  return Boolean(
    !activeScan || !['COMPLETED', 'FAILED', 'CANCELLED'].includes(activeScan.status)
  );
}
