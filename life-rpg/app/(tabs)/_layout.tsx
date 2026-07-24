import React from 'react';
import { Tabs } from 'expo-router';
import BottomNavigation from '../../components/BottomNavigation';

// Bottom tab navigator using the custom BottomNavigation bar.
export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{ headerShown: false }}
      tabBar={(props) => <BottomNavigation {...(props as any)} />}
    >
      <Tabs.Screen name="index" options={{ title: 'Inicio' }} />
      <Tabs.Screen name="habits" options={{ title: 'Hábitos' }} />
      <Tabs.Screen name="shop" options={{ title: 'Tienda' }} />
      <Tabs.Screen name="profile" options={{ title: 'Perfil' }} />
    </Tabs>
  );
}
