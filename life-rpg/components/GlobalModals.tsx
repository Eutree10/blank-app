import React from 'react';
import { usePlayer } from '../context/PlayerContext';
import LevelUpModal from './LevelUpModal';
import LifeZeroModal from './LifeZeroModal';

// Renders the app-wide modals that can appear on top of any screen.
export default function GlobalModals() {
  const { pendingLevelUp, clearLevelUp, lifeZero, confirmPunishment } = usePlayer();

  return (
    <>
      <LevelUpModal
        visible={pendingLevelUp !== null}
        level={pendingLevelUp ?? 1}
        onClose={clearLevelUp}
      />
      <LifeZeroModal visible={lifeZero} onConfirm={confirmPunishment} />
    </>
  );
}
