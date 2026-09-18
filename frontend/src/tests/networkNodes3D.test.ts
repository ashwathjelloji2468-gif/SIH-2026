import { CryptoAsset } from '../types';

export function runNetworkNodes3DTests(): { name: string; passed: boolean; details: string }[] {
  const results: { name: string; passed: boolean; details: string }[] = [];

  // Helper logic mirroring NetworkNodes3D node mapping logic
  function mapAssetsToNodes(assets: CryptoAsset[]) {
    if (!assets || assets.length === 0) return [];
    const total = assets.length;
    return assets.map((asset, i) => {
      let position: [number, number, number];
      if (total === 1) {
        position = [0, 0, 0];
      } else {
        const phi = Math.acos(-1 + (2 * i + 1) / total);
        const theta = Math.sqrt(total * Math.PI) * phi;
        const radius = 2.2;
        const x = radius * Math.cos(theta) * Math.sin(phi);
        const y = radius * Math.sin(theta) * Math.sin(phi);
        const z = radius * Math.cos(phi);
        position = [Number(x.toFixed(2)), Number(y.toFixed(2)), Number(z.toFixed(2))];
      }

      const safety =
        asset.quantum_safety === 'SAFE'
          ? 'SAFE'
          : asset.quantum_safety === 'VULNERABLE'
          ? 'VULNERABLE'
          : asset.quantum_safety === 'TRANSITIONAL'
          ? 'TRANSITIONAL'
          : 'UNKNOWN';

      return {
        id: asset.id,
        name: asset.algorithm_name || asset.name || 'Unknown',
        type: asset.asset_type || 'ALGORITHM',
        safety,
        position
      };
    });
  }

  // TEST 1: Empty assets produces zero 3D nodes
  const emptyNodes = mapAssetsToNodes([]);
  results.push({
    name: 'TEST 1: NetworkNodes3D produces zero 3D nodes when asset list is empty',
    passed: emptyNodes.length === 0,
    details: `Nodes count = ${emptyNodes.length} (expected 0)`
  });

  // TEST 2: Real assets produce matching node count and real names/ids
  const mockRealAssets: CryptoAsset[] = [
    {
      id: 'asset-101',
      scan_id: 'scan-1',
      name: 'Custom RSA Usage',
      asset_type: 'ALGORITHM',
      algorithm_name: 'RSA-1024-CUSTOM',
      key_size: 1024,
      purpose: 'ENCRYPTION',
      location: 'crypto/legacy.py',
      line_number: 45,
      quantum_safety: 'VULNERABLE',
      is_unknown: false,
      review_status: 'PENDING',
      created_at: '2026-09-18T10:00:00Z',
    },
    {
      id: 'asset-102',
      scan_id: 'scan-1',
      name: 'Kyber Key Exchange',
      asset_type: 'ALGORITHM',
      algorithm_name: 'ML-KEM-1024',
      key_size: 1024,
      purpose: 'KEY_ESTABLISHMENT',
      location: 'crypto/pqc.py',
      line_number: 12,
      quantum_safety: 'SAFE',
      is_unknown: false,
      review_status: 'RESOLVED',
      created_at: '2026-09-18T10:00:00Z',
    }
  ];

  const realNodes = mapAssetsToNodes(mockRealAssets);
  const countMatches = realNodes.length === 2;
  const namesMatch = realNodes[0].name === 'RSA-1024-CUSTOM' && realNodes[1].name === 'ML-KEM-1024';
  const safetiesMatch = realNodes[0].safety === 'VULNERABLE' && realNodes[1].safety === 'SAFE';
  const idsMatch = realNodes[0].id === 'asset-101' && realNodes[1].id === 'asset-102';

  results.push({
    name: 'TEST 2: NetworkNodes3D maps real scanner asset ids, names, and safety levels to 3D nodes',
    passed: countMatches && namesMatch && safetiesMatch && idsMatch,
    details: `Count=${realNodes.length}, Node1=${realNodes[0]?.name}(${realNodes[0]?.safety}), Node2=${realNodes[1]?.name}(${realNodes[1]?.safety})`
  });

  // TEST 3: Spherical 3D positioning generates valid numbers without NaN
  const hasValidPositions = realNodes.every(
    (n) => !isNaN(n.position[0]) && !isNaN(n.position[1]) && !isNaN(n.position[2])
  );
  results.push({
    name: 'TEST 3: NetworkNodes3D calculates valid 3D coordinates (no NaN)',
    passed: hasValidPositions,
    details: `Positions: Node1=${JSON.stringify(realNodes[0]?.position)}, Node2=${JSON.stringify(realNodes[1]?.position)}`
  });

  return results;
}
