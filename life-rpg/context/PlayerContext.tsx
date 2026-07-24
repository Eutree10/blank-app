import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { Habit, PlayerState, Reward } from '../types';
import { createInitialState, loadState, saveState, clearState } from '../storage/storage';
import { applyXp, xpForLevel, isMaxLevel } from '../utils/level';
import { clamp } from '../utils/num';
import { todayKey } from '../utils/date';
import { uid } from '../utils/id';
import { MAX_LIFE, STARTING_LIFE } from '../constants/game';

interface PlayerContextValue {
  state: PlayerState;
  loading: boolean;
  // derived helpers
  xpNeeded: number;
  maxLevel: boolean;
  // modal state
  pendingLevelUp: number | null; // new level to celebrate, or null
  clearLevelUp: () => void;
  lifeZero: boolean;
  // actions
  completeGoodHabit: (id: string) => void;
  registerBadHabit: (id: string) => void;
  addHabit: (habit: Omit<Habit, 'id'>) => void;
  updateHabit: (habit: Habit) => void;
  deleteHabit: (id: string) => void;
  buyReward: (id: string) => { ok: boolean; message: string };
  addReward: (reward: Omit<Reward, 'id'>) => void;
  deleteReward: (id: string) => void;
  toggleSound: () => void;
  confirmPunishment: () => void;
  resetProgress: () => void;
}

const PlayerContext = createContext<PlayerContextValue | undefined>(undefined);

export function PlayerProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<PlayerState>(createInitialState);
  const [loading, setLoading] = useState(true);
  const [pendingLevelUp, setPendingLevelUp] = useState<number | null>(null);
  const hydrated = useRef(false);

  // Load persisted state on mount and apply day rollover.
  useEffect(() => {
    (async () => {
      const loaded = await loadState();
      const today = todayKey();
      if (loaded.lastActiveDate !== today) {
        // New day: reset only the daily habit completions and count a new active day.
        loaded.completedToday = [];
        loaded.stats.activeDays += 1;
        loaded.lastActiveDate = today;
      }
      setState(loaded);
      hydrated.current = true;
      setLoading(false);
    })();
  }, []);

  // Persist whenever state changes (after initial hydration).
  useEffect(() => {
    if (!hydrated.current) return;
    saveState(state);
  }, [state]);

  const completeGoodHabit = useCallback((id: string) => {
    setState((prev) => {
      const habit = prev.habits.find((h) => h.id === id);
      if (!habit || habit.type !== 'good') return prev;
      if (prev.completedToday.includes(id)) return prev;

      const result = applyXp(prev.stats.level, prev.stats.xp, habit.xp);
      if (result.leveledUp) {
        // Defer modal update out of the setState updater.
        setPendingLevelUp(result.level);
      }
      return {
        ...prev,
        stats: {
          ...prev.stats,
          level: result.level,
          xp: result.xp,
          coins: prev.stats.coins + habit.coins,
          totalXp: prev.stats.totalXp + habit.xp,
          habitsCompleted: prev.stats.habitsCompleted + 1,
        },
        completedToday: [...prev.completedToday, id],
      };
    });
  }, []);

  const registerBadHabit = useCallback((id: string) => {
    setState((prev) => {
      const habit = prev.habits.find((h) => h.id === id);
      if (!habit || habit.type !== 'bad') return prev;
      if (prev.completedToday.includes(id)) return prev;

      const newLife = clamp(prev.stats.life - habit.lifePenalty, 0, MAX_LIFE);
      return {
        ...prev,
        stats: { ...prev.stats, life: newLife },
        completedToday: [...prev.completedToday, id],
      };
    });
  }, []);

  const addHabit = useCallback((habit: Omit<Habit, 'id'>) => {
    setState((prev) => ({
      ...prev,
      habits: [...prev.habits, { ...habit, id: uid('h') }],
    }));
  }, []);

  const updateHabit = useCallback((habit: Habit) => {
    setState((prev) => ({
      ...prev,
      habits: prev.habits.map((h) => (h.id === habit.id ? habit : h)),
    }));
  }, []);

  const deleteHabit = useCallback((id: string) => {
    setState((prev) => ({
      ...prev,
      habits: prev.habits.filter((h) => h.id !== id),
      completedToday: prev.completedToday.filter((c) => c !== id),
    }));
  }, []);

  const buyReward = useCallback((id: string): { ok: boolean; message: string } => {
    let outcome = { ok: false, message: 'No tienes suficientes monedas' };
    setState((prev) => {
      const reward = prev.rewards.find((r) => r.id === id);
      if (!reward) return prev;
      if (prev.stats.coins < reward.price) {
        outcome = { ok: false, message: 'No tienes suficientes monedas' };
        return prev;
      }
      const newLife =
        reward.type === 'life'
          ? clamp(prev.stats.life + reward.lifeAmount, 0, MAX_LIFE)
          : prev.stats.life;
      outcome = { ok: true, message: 'Recompensa comprada' };
      return {
        ...prev,
        stats: {
          ...prev.stats,
          coins: prev.stats.coins - reward.price,
          life: newLife,
        },
        purchases: [
          ...prev.purchases,
          { id: uid('p'), rewardName: reward.name, price: reward.price, date: todayKey() },
        ],
      };
    });
    return outcome;
  }, []);

  const addReward = useCallback((reward: Omit<Reward, 'id'>) => {
    setState((prev) => ({
      ...prev,
      rewards: [...prev.rewards, { ...reward, id: uid('r') }],
    }));
  }, []);

  const deleteReward = useCallback((id: string) => {
    setState((prev) => ({
      ...prev,
      rewards: prev.rewards.filter((r) => r.id !== id),
    }));
  }, []);

  const toggleSound = useCallback(() => {
    setState((prev) => ({ ...prev, soundEnabled: !prev.soundEnabled }));
  }, []);

  const confirmPunishment = useCallback(() => {
    setState((prev) => ({
      ...prev,
      stats: { ...prev.stats, life: STARTING_LIFE },
    }));
  }, []);

  const resetProgress = useCallback(() => {
    (async () => {
      await clearState();
    })();
    setPendingLevelUp(null);
    setState(createInitialState());
  }, []);

  const clearLevelUp = useCallback(() => setPendingLevelUp(null), []);

  const xpNeeded = xpForLevel(state.stats.level);
  const maxLevel = isMaxLevel(state.stats.level);
  const lifeZero = state.stats.life <= 0;

  const value = useMemo<PlayerContextValue>(
    () => ({
      state,
      loading,
      xpNeeded,
      maxLevel,
      pendingLevelUp,
      clearLevelUp,
      lifeZero,
      completeGoodHabit,
      registerBadHabit,
      addHabit,
      updateHabit,
      deleteHabit,
      buyReward,
      addReward,
      deleteReward,
      toggleSound,
      confirmPunishment,
      resetProgress,
    }),
    [
      state,
      loading,
      xpNeeded,
      maxLevel,
      pendingLevelUp,
      clearLevelUp,
      lifeZero,
      completeGoodHabit,
      registerBadHabit,
      addHabit,
      updateHabit,
      deleteHabit,
      buyReward,
      addReward,
      deleteReward,
      toggleSound,
      confirmPunishment,
      resetProgress,
    ]
  );

  return <PlayerContext.Provider value={value}>{children}</PlayerContext.Provider>;
}

export function usePlayer(): PlayerContextValue {
  const ctx = useContext(PlayerContext);
  if (!ctx) throw new Error('usePlayer must be used within a PlayerProvider');
  return ctx;
}
