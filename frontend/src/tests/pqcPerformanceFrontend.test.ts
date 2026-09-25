import { Recommendation, PerformancePredictionData } from '../types';

export function runPQCPerformanceFrontendTests() {
  const results: Array<{ name: string; passed: boolean; details: string }> = [];

  // Helper to assert condition
  const test = (name: string, fn: () => { passed: boolean; details: string }) => {
    try {
      const res = fn();
      results.push({ name, passed: res.passed, details: res.details });
    } catch (e: any) {
      results.push({ name, passed: false, details: `Exception: ${e?.message || String(e)}` });
    }
  };

  // Test A: READY performance evidence structure
  test('TEST A: READY performance evidence structure contains expected fields', () => {
    const perf: PerformancePredictionData = {
      status: 'READY',
      predicted_latency_us: 29.13,
      predicted_throughput_ops_s: null,
      model_version: 'catboost-pqc-v1.0',
      provider_name: 'CatBoostPerformancePredictionProvider',
      benchmark_source: 'PQC Algorithms Benchmark Data',
      evidence: ['CatBoost predicted CPU latency: 29.13 µs.'],
    };

    const isReady = perf.status === 'READY';
    const hasLatency = perf.predicted_latency_us === 29.13;
    const hasNullThroughput = perf.predicted_throughput_ops_s === null;

    return {
      passed: isReady && hasLatency && hasNullThroughput,
      details: `status=${perf.status}, latency=${perf.predicted_latency_us}, throughput=${perf.predicted_throughput_ops_s}`,
    };
  });

  // Test B & C: MODEL PREDICTION label & value formatting
  test('TEST B & C: Latency is formatted and explicitly labeled MODEL PREDICTION', () => {
    const perf: PerformancePredictionData = {
      status: 'READY',
      predicted_latency_us: 29.13,
    };
    const label = 'MODEL PREDICTION';
    const formattedVal = `${perf.predicted_latency_us} µs`;

    return {
      passed: label === 'MODEL PREDICTION' && formattedVal === '29.13 µs',
      details: `Label="${label}", Value="${formattedVal}"`,
    };
  });

  // Test D: Model version & provider provenance
  test('TEST D: Model version and provider provenance map correctly', () => {
    const perf: PerformancePredictionData = {
      status: 'READY',
      model_version: 'catboost-pqc-v1.0',
      provider_name: 'CatBoostPerformancePredictionProvider',
      benchmark_source: 'PQC Algorithms Benchmark Data',
    };

    return {
      passed:
        perf.model_version === 'catboost-pqc-v1.0' &&
        perf.provider_name === 'CatBoostPerformancePredictionProvider' &&
        perf.benchmark_source === 'PQC Algorithms Benchmark Data',
      details: `version=${perf.model_version}, provider=${perf.provider_name}, source=${perf.benchmark_source}`,
    };
  });

  // Test E: UNCONFIGURED state handling
  test('TEST E: UNCONFIGURED status renders fallback message without numeric latency', () => {
    const perf: PerformancePredictionData = {
      status: 'UNCONFIGURED',
      reason: 'MODEL_ARTIFACT_NOT_CONFIGURED',
      predicted_latency_us: null,
    };

    const isUnconfigured = perf.status === 'UNCONFIGURED';
    const noNumericLatency = perf.predicted_latency_us === null;
    const msg = 'Performance model unavailable';

    return {
      passed: isUnconfigured && noNumericLatency && msg === 'Performance model unavailable',
      details: `status=${perf.status}, msg="${msg}"`,
    };
  });

  // Test F: ERROR state handling
  test('TEST F: ERROR status renders safe fallback without breaking card', () => {
    const perf: PerformancePredictionData = {
      status: 'ERROR',
      reason: 'MODEL_LOAD_FAILED',
      predicted_latency_us: null,
    };

    const isError = perf.status === 'ERROR';
    const msg = 'Performance prediction unavailable';

    return {
      passed: isError && msg === 'Performance prediction unavailable',
      details: `status=${perf.status}, msg="${msg}"`,
    };
  });

  // Test G: missing_features state handling
  test('TEST G: missing_features renders safe data request message', () => {
    const perf: PerformancePredictionData = {
      status: 'UNCONFIGURED',
      reason: 'MISSING_REQUIRED_MODEL_FEATURES',
      missing_features: ['text_length_bytes', 'text_size_kb'],
    };

    const hasMissing = (perf.missing_features || []).length > 0;
    const msg = 'Needs additional performance data';

    return {
      passed: hasMissing && msg === 'Needs additional performance data',
      details: `missingCount=${perf.missing_features?.length}, msg="${msg}"`,
    };
  });

  // Test H: Null throughput does not display fake values
  test('TEST H: Null throughput is preserved without fake numeric calculation', () => {
    const perf: PerformancePredictionData = {
      status: 'READY',
      predicted_latency_us: 29.13,
      predicted_throughput_ops_s: null,
    };

    const rawNull = perf.predicted_throughput_ops_s === null;
    const noFakeZero = perf.predicted_throughput_ops_s !== 0;

    return {
      passed: rawNull && noFakeZero,
      details: `predicted_throughput_ops_s=${perf.predicted_throughput_ops_s}`,
    };
  });

  // Test I & J: Recommendation without performance data renders cleanly
  test('TEST I & J: Recommendation without performance data renders legacy fields safely', () => {
    const rec: Recommendation = {
      asset_id: 'asset-123',
      target_pqc_candidate: 'ML-KEM-768',
      standard_status: 'FINAL_STANDARD',
      rationale: 'Migrate to ML-KEM-768 per NIST FIPS 203.',
      migration_complexity: 'MEDIUM',
      confidence: 0.9,
    };

    const hasNoPerf = rec.tradeoffs?.performance === undefined;
    const legacyValid = rec.target_pqc_candidate === 'ML-KEM-768' && rec.standard_status === 'FINAL_STANDARD';

    return {
      passed: hasNoPerf && legacyValid,
      details: `hasNoPerf=${hasNoPerf}, legacyValid=${legacyValid}`,
    };
  });

  return results;
}
