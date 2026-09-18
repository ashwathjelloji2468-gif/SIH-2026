import { riskService } from '../services/riskService';
import { api } from '../services/api';

export function runRiskAssessmentTimeoutTests(): { name: string; passed: boolean; details: string }[] {
  const results: { name: string; passed: boolean; details: string }[] = [];

  const originalPost = api.post;
  let capturedEndpoint = '';
  let capturedBody: any = null;
  let capturedOptions: any = null;

  api.post = async (endpoint: string, body?: any, options?: any) => {
    capturedEndpoint = endpoint;
    capturedBody = body;
    capturedOptions = options;
    return [] as any;
  };

  try {
    // TEST 1: assessProjectRisk passes timeoutMs = 240000 and endpoint /projects/{projectId}/risk/assess
    riskService.assessProjectRisk('proj-test-123');

    const is240k = capturedOptions?.timeoutMs === 240000;
    const isEndpointCorrect = capturedEndpoint === '/projects/proj-test-123/risk/assess';

    results.push({
      name: 'TEST 1: assessProjectRisk uses timeoutMs = 240000 and endpoint /projects/{projectId}/risk/assess',
      passed: is240k && isEndpointCorrect,
      details: `timeoutMs=${capturedOptions?.timeoutMs}, endpoint=${capturedEndpoint}`,
    });
  } finally {
    api.post = originalPost;
  }

  return results;
}

const res = runRiskAssessmentTimeoutTests();
console.log('=== RUNNING FRONTEND RISK ASSESSMENT TIMEOUT TEST ===');
res.forEach((r) => console.log(`${r.passed ? '✓ [PASS]' : '✗ [FAIL]'} ${r.name} (${r.details})`));
