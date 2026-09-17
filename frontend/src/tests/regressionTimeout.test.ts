import { validationService } from '../services/validationService';
import { api } from '../services/api';

export function runRegressionTimeoutTests(): { name: string; passed: boolean; details: string }[] {
  const results: { name: string; passed: boolean; details: string }[] = [];

  const originalPost = api.post;
  let capturedEndpoint = '';
  let capturedBody: any = null;
  let capturedOptions: any = null;

  api.post = async (endpoint: string, body?: any, options?: any) => {
    capturedEndpoint = endpoint;
    capturedBody = body;
    capturedOptions = options;
    return { status: 'NO_REGRESSION' } as any;
  };

  try {
    // TEST 1: runRegressionValidation passes timeoutMs = 240000
    validationService.runRegressionValidation('proj-123', { scanId: 'scan-456' });

    const is240k = capturedOptions?.timeoutMs === 240000;
    const isEndpointCorrect = capturedEndpoint === '/projects/proj-123/validation/regression?scan_id=scan-456';

    results.push({
      name: 'TEST 1: runRegressionValidation uses timeoutMs = 240000',
      passed: is240k && isEndpointCorrect,
      details: `timeoutMs=${capturedOptions?.timeoutMs}, endpoint=${capturedEndpoint}`,
    });

    // TEST 2: runBuildValidation does NOT set custom timeoutMs (preserves default timeout)
    capturedOptions = null;
    validationService.runBuildValidation('proj-123', { scanId: 'scan-456' });

    const isBuildTimeoutDefault = capturedOptions?.timeoutMs === undefined;
    results.push({
      name: 'TEST 2: runBuildValidation preserves default timeout (timeoutMs undefined)',
      passed: isBuildTimeoutDefault,
      details: `timeoutMs=${capturedOptions?.timeoutMs}`,
    });

    // TEST 3: runTestValidation does NOT set custom timeoutMs (preserves default timeout)
    capturedOptions = null;
    validationService.runTestValidation('proj-123', { scanId: 'scan-456' });

    const isTestTimeoutDefault = capturedOptions?.timeoutMs === undefined;
    results.push({
      name: 'TEST 3: runTestValidation preserves default timeout (timeoutMs undefined)',
      passed: isTestTimeoutDefault,
      details: `timeoutMs=${capturedOptions?.timeoutMs}`,
    });
  } finally {
    api.post = originalPost;
  }

  return results;
}
