// Core domain types for Life RPG

export type HabitType = 'good' | 'bad';

export interface Habit {
  id: string;
  name: string;
  type: HabitType;
  icon: string; // key from ICONS
  xp: number; // reward when good
  coins: number; // reward when good
  lifePenalty: number; // life lost when bad
}

export type RewardType = 'normal' | 'life';

export interface Reward {
  id: string;
  name: string;
  icon: string; // key from ICONS
  price: number;
  type: RewardType;
  lifeAmount: number; // only used when type === 'life'
}

export interface PlayerStats {
  level: number;
  xp: number; // current xp toward next level
  coins: number;
  life: number;
  totalXp: number; // lifetime xp earned
  habitsCompleted: number; // lifetime count
  activeDays: number; // number of distinct days the app was used
}

export interface PlayerState {
  stats: PlayerStats;
  habits: Habit[];
  rewards: Reward[];
  // ids of habits marked today, reset on a new day
  completedToday: string[];
  // list of purchase records (reward name + price)
  purchases: Purchase[];
  soundEnabled: boolean;
  lastActiveDate: string; // YYYY-MM-DD
}

export interface Purchase {
  id: string;
  rewardName: string;
  price: number;
  date: string; // YYYY-MM-DD
}
