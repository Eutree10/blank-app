import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { Stack } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { PlayerProvider } from '../context/PlayerContext';
import GlobalModals from '../components/GlobalModals';
import { COLORS } from '../constants/colors';

// Root layout: wraps the whole app in the player state provider and
// renders the global level-up / life-zero modals above every screen.
export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <PlayerProvider>
        <StatusBar style="dark" />
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: COLORS.background },
          }}
        >
          <Stack.Screen name="(tabs)" />
        </Stack>
        <GlobalModals />
      </PlayerProvider>
    </SafeAreaProvider>
  );
}
