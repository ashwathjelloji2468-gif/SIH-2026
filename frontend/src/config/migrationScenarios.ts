import { MigrationScenario, YScenarioKey } from '../types/yEngine';

export const DEFAULT_Y_SCENARIO_KEY: YScenarioKey = 'STANDARD';
export const DEFAULT_Y_YEARS_VALUE = 10;

export const MIGRATION_SCENARIOS_LIST: MigrationScenario[] = [
  {
    key: 'FAST',
    title: 'Fast / Simple Migration',
    value: 5,
    description: 'Modern codebase with single language, automated CI/CD pipelines, and minimal external dependencies.',
    details: 'Suitable for greenfield SaaS services, microservices with high test coverage, and modern cloud-native apps with no hardware or legacy dependencies.'
  },
  {
    key: 'STANDARD',
    title: 'Standard Enterprise Migration',
    value: 10,
    description: 'Standardized migration planning assumption for average enterprise software applications.',
    details: 'Default MVP planning scenario for typical corporate web apps with moderate dependency trees, standard refactoring lifecycles, and phased deployment windows.'
  },
  {
    key: 'COMPLEX',
    title: 'Complex Distributed Migration',
    value: 15,
    description: 'Multi-service distributed architecture with third-party vendor APIs, database encryption, and hardware HSMs.',
    details: 'Designed for complex multi-tier platforms requiring cross-team coordination, vendor SLA updates, hybrid PQC algorithm testing, and extended compliance audits.'
  },
  {
    key: 'LEGACY_HEAVY',
    title: 'Highly Complex / Legacy-Heavy',
    value: 20,
    description: 'Monolithic legacy infrastructure, embedded firmware, regulated banking/government core, or mainframe systems.',
    details: 'Appropriate for mission-critical legacy infrastructure where cryptographic primitives are deeply embedded in hardware, custom protocols, or long-term operational contracts.'
  }
];

export function getMigrationScenarioByKey(key: string): MigrationScenario {
  const upper = key.toUpperCase();
  return MIGRATION_SCENARIOS_LIST.find(s => s.key === upper) || MIGRATION_SCENARIOS_LIST[1];
}
