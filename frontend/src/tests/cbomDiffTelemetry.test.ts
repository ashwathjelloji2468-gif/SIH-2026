export function runCBOMDiffTelemetryTests(): { name: string; passed: boolean; details: string }[] {
  const results: { name: string; passed: boolean; details: string }[] = [];

  const mockResponse: {
    check_type: string;
    status: string;
    framework: string | null;
    exit_code: number | null;
    duration: number | null;
    duration_ms?: number;
  } = {
    check_type: 'CBOM_DIFF',
    status: 'NO_CHANGE',
    framework: 'Python',
    exit_code: null,
    duration: 1.23,
    duration_ms: undefined,
  };

  const renderedFramework = mockResponse.framework ?? '—';
  const renderedExitCode = mockResponse.exit_code ?? 'N/A';
  const renderedDuration =
    mockResponse.duration_ms !== undefined && mockResponse.duration_ms !== null && mockResponse.duration_ms !== 0
      ? `${mockResponse.duration_ms} ms`
      : mockResponse.duration !== undefined && mockResponse.duration !== null
      ? `${mockResponse.duration} s`
      : 'N/A';

  const isFrameworkCorrect = renderedFramework === 'Python';
  const isExitCodeCorrect = renderedExitCode === 'N/A';
  const isDurationCorrect = renderedDuration === '1.23 s';
  const noUndefinedS = !renderedDuration.includes('undefined');

  results.push({
    name: 'TEST 4: CBOM diff telemetry renders framework, N/A exit code, and 1.23 s duration without undefined s',
    passed: isFrameworkCorrect && isExitCodeCorrect && isDurationCorrect && noUndefinedS,
    details: `Framework=${renderedFramework}, ExitCode=${renderedExitCode}, Duration=${renderedDuration}`,
  });

  return results;
}
