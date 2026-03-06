import React, { useState, useEffect } from 'react';
import { Box, Text, useInput, useApp } from 'ink';
import SelectInput from 'ink-select-input';
import Spinner from 'ink-spinner';
import { api, Profile } from './api.js';
import { ComposeScreen, ConfigScreen, HistoryScreen, SendingScreen } from './screens.js';

type Screen = 'menu' | 'compose' | 'history' | 'config' | 'sending';

export const App = () => {
  const { exit } = useApp();
  const [currentScreen, setCurrentScreen] = useState<Screen>('menu');
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [activeProfile, setActiveProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadProfiles = async () => {
    try {
      setLoading(true);
      const all = await api.getProfiles();
      const active = await api.getActiveProfile();
      setProfiles(all);
      setActiveProfile(active);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Error loading profiles');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfiles();
  }, []);

  useInput((input, key) => {
    if (key.escape || (input === 'q' && currentScreen === 'menu')) {
      if (currentScreen === 'menu') {
        exit();
      } else {
        setCurrentScreen('menu');
      }
    }
  });

  if (loading) {
    return <Box><Text><Spinner type="dots" /> Loading...</Text></Box>;
  }

  if (error) {
    return <Box><Text color="red">Error: {error}</Text></Box>;
  }

  return (
    <Box flexDirection="column" padding={1} width="100%">
      <Box borderStyle="round" borderColor="blue" padding={1} flexDirection="column">
        <Text bold color="cyan">SES Email Sender TUI</Text>
        <Text color="gray">Active Profile: {activeProfile?.name || 'None'}</Text>
      </Box>

      <Box marginTop={1} flexGrow={1}>
        {currentScreen === 'menu' && <MainMenu setScreen={setCurrentScreen} />}
        {currentScreen === 'compose' && <ComposeScreen setScreen={setCurrentScreen} />}
        {currentScreen === 'history' && <HistoryScreen setScreen={setCurrentScreen} />}
        {currentScreen === 'config' && (
          <ConfigScreen
            profiles={profiles}
            activeProfile={activeProfile!}
            onUpdate={loadProfiles}
            setScreen={setCurrentScreen}
          />
        )}
        {currentScreen === 'sending' && <SendingScreen setScreen={setCurrentScreen} />}
      </Box>
      <Box marginTop={1}>
        <Text color="gray">Press Esc to return / Q to quit (in menu)</Text>
      </Box>
    </Box>
  );
};

const MainMenu = ({ setScreen }: { setScreen: (s: Screen) => void }) => {
  const items = [
    { label: 'Compose Email', value: 'compose' },
    { label: 'Configuration & Profiles', value: 'config' },
    { label: 'History', value: 'history' },
    { label: 'Quit', value: 'quit' }
  ];

  const handleSelect = (item: { value: string }) => {
    if (item.value === 'quit') {
      process.exit(0);
    } else {
      setScreen(item.value as Screen);
    }
  };

  return (
    <Box flexDirection="column">
      <Text bold marginBottom={1}>Main Menu</Text>
      {/* @ts-ignore */}
      <SelectInput items={items} onSelect={handleSelect} />
    </Box>
  );
};
