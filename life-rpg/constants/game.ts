// Global game constants.
export const MAX_LIFE = 1000;
export const MAX_LEVEL = 46;
export const STARTING_LIFE = 1000;

// Rank thresholds by level range.
export const RANKS: { min: number; max: number; name: string }[] = [
  { min: 1, max: 5, name: 'Aprendiz' },
  { min: 6, max: 10, name: 'Explorador' },
  { min: 11, max: 20, name: 'Aventurero' },
  { min: 21, max: 30, name: 'Héroe' },
  { min: 31, max: 40, name: 'Maestro' },
  { min: 41, max: 46, name: 'Gran Maestro' },
];

// The single fixed punishment used when life reaches 0.
export const PUNISHMENT_TEXT = 'Completa 100 push-ups para recuperar tu vida';
