import { MAX_LEVEL, RANKS } from '../constants/game';

// XP required to advance FROM `level` to `level + 1`.
// Formula: round(100 * 1.2^(level - 1)).
export function xpForLevel(level: number): number {
  return Math.round(100 * Math.pow(1.2, level - 1));
}

export function isMaxLevel(level: number): boolean {
  return level >= MAX_LEVEL;
}

export function rankForLevel(level: number): string {
  const rank = RANKS.find((r) => level >= r.min && level <= r.max);
  return rank ? rank.name : RANKS[RANKS.length - 1].name;
}

export interface LevelUpResult {
  level: number;
  xp: number;
  leveledUp: boolean;
  levelsGained: number;
}

// Apply earned XP to a level/xp pair, processing multiple level-ups.
// Stops accumulating XP once max level is reached.
export function applyXp(level: number, xp: number, gained: number): LevelUpResult {
  let newLevel = level;
  let newXp = xp + gained;
  let levelsGained = 0;

  while (!isMaxLevel(newLevel) && newXp >= xpForLevel(newLevel)) {
    newXp -= xpForLevel(newLevel);
    newLevel += 1;
    levelsGained += 1;
  }

  // At max level, XP no longer accumulates toward a next level.
  if (isMaxLevel(newLevel)) {
    newXp = 0;
  }

  return {
    level: newLevel,
    xp: newXp,
    leveledUp: levelsGained > 0,
    levelsGained,
  };
}
