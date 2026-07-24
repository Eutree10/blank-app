import { Habit, Reward } from '../types';

// Preloaded good and bad habits.
export const INITIAL_HABITS: Habit[] = [
  { id: 'h_water', name: 'Beber agua', type: 'good', icon: '💧', xp: 10, coins: 5, lifePenalty: 0 },
  { id: 'h_exercise', name: 'Hacer ejercicio', type: 'good', icon: '🏃', xp: 30, coins: 15, lifePenalty: 0 },
  { id: 'h_study', name: 'Estudiar', type: 'good', icon: '📚', xp: 20, coins: 10, lifePenalty: 0 },
  { id: 'h_wakeup', name: 'Despertarse temprano', type: 'good', icon: '⏰', xp: 15, coins: 8, lifePenalty: 0 },
  { id: 'h_read', name: 'Leer', type: 'good', icon: '📖', xp: 15, coins: 8, lifePenalty: 0 },
  { id: 'h_procrastinate', name: 'Procrastinar', type: 'bad', icon: '📱', xp: 0, coins: 0, lifePenalty: 100 },
  { id: 'h_littlesleep', name: 'Dormir poco', type: 'bad', icon: '🛏️', xp: 0, coins: 0, lifePenalty: 100 },
  { id: 'h_junkfood', name: 'Comer comida chatarra', type: 'bad', icon: '🍔', xp: 0, coins: 0, lifePenalty: 75 },
];

// Preloaded shop rewards.
export const INITIAL_REWARDS: Reward[] = [
  { id: 'r_movie', name: 'Ver una película', icon: '🎬', price: 100, type: 'normal', lifeAmount: 0 },
  { id: 'r_soda', name: 'Tomar una gaseosa', icon: '🥤', price: 70, type: 'normal', lifeAmount: 0 },
  { id: 'r_fries', name: 'Comer papas fritas', icon: '🍟', price: 80, type: 'normal', lifeAmount: 0 },
  { id: 'r_game', name: 'Jugar 30 minutos', icon: '🎮', price: 120, type: 'normal', lifeAmount: 0 },
  { id: 'r_break', name: 'Descanso de 20 minutos', icon: '☕', price: 60, type: 'normal', lifeAmount: 0 },
  { id: 'r_life', name: 'Recuperar 200 de vida', icon: '❤️', price: 100, type: 'life', lifeAmount: 200 },
];
