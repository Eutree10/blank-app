// Central color palette. Light, slightly warm background; red as the primary color.
export const COLORS = {
  primary: '#E23B3B', // main red
  primaryDark: '#B71C1C', // damage / bad habits
  background: '#FBF6F0', // light warm background
  card: '#FFFFFF',
  border: '#EFE7DE',
  textDark: '#3A3A3A', // dark gray text
  textMuted: '#8A8279',
  gold: '#F2B705', // coins & xp
  green: '#3FA34D', // positive actions
  greenDark: '#2E7D32',
  shadow: '#000000',
  white: '#FFFFFF',
  overlay: 'rgba(0,0,0,0.5)',
  lifeTrack: '#F0DADA',
  xpTrack: '#F1E4C4',
} as const;

export type ColorKey = keyof typeof COLORS;
