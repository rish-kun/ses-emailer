import React, { useState, useEffect } from 'react';
import { Box, Text, useInput, useApp } from 'ink';
import SelectInput from 'ink-select-input';
import TextInput from 'ink-text-input';
import Spinner from 'ink-spinner';
import { api, Profile, AppConfig } from './api.js';

type Screen = 'menu' | 'compose' | 'history' | 'config' | 'sending';

// ... (omitted MainMenu and App boilerplate for brevity)

export const ConfigScreen = ({ profiles, activeProfile, onUpdate, setScreen }: { profiles: Profile[], activeProfile: Profile, onUpdate: () => void, setScreen: (s: Screen) => void }) => {
  const [view, setView] = useState<'list' | 'edit'>('list');
  const [editingConfig, setEditingConfig] = useState<AppConfig | null>(null);
  const [editingName, setEditingName] = useState('');
  const [fieldIndex, setFieldIndex] = useState(0);

  const items = profiles.map(p => ({ label: `${p.name} ${p.id === activeProfile.id ? '(Active)' : ''}`, value: p.id }));
  items.push({ label: 'Create New Profile', value: 'new' });

  const handleSelect = async (item: { value: string }) => {
    if (item.value === 'new') {
      await api.createProfile(`New Profile ${profiles.length + 1}`);
      onUpdate();
    } else {
      if (item.value !== activeProfile.id) {
        await api.setActiveProfile(item.value);
        onUpdate();
      }
      setView('edit');
      const p = profiles.find(p => p.id === item.value)!;
      setEditingName(p.name);
      setEditingConfig(JSON.parse(JSON.stringify(p.config)));
    }
  };

  useInput((input, key) => {
    if (view === 'edit' && key.escape) {
      setView('list');
    }
    if (view === 'edit' && key.return) {
      api.updateProfile(activeProfile.id, editingName, editingConfig!).then(() => {
        onUpdate();
        setView('list');
      });
    }
  });

  if (view === 'list') {
    return (
      <Box flexDirection="column">
        <Text bold>Select or Create Profile</Text>
        // @ts-ignore
        <SelectInput items={items} onSelect={handleSelect} />
      </Box>
    );
  }

  return (
    <Box flexDirection="column">
      <Text bold color="yellow">Editing Profile</Text>
      <Text>Profile Name:</Text>
      // @ts-ignore
      <TextInput value={editingName} onChange={setEditingName} />
      <Text>AWS Access Key:</Text>
      // @ts-ignore
      <TextInput value={editingConfig?.aws.access_key_id || ''} onChange={(v) => setEditingConfig({ ...editingConfig!, aws: { ...editingConfig!.aws, access_key_id: v } })} />
      <Text>AWS Secret Key:</Text>
      // @ts-ignore
      <TextInput value={editingConfig?.aws.secret_access_key || ''} onChange={(v) => setEditingConfig({ ...editingConfig!, aws: { ...editingConfig!.aws, secret_access_key: v } })} />
      <Text>AWS Region:</Text>
      // @ts-ignore
      <TextInput value={editingConfig?.aws.region || ''} onChange={(v) => setEditingConfig({ ...editingConfig!, aws: { ...editingConfig!.aws, region: v } })} />
      <Text>Source Email:</Text>
      // @ts-ignore
      <TextInput value={editingConfig?.aws.source_email || ''} onChange={(v) => setEditingConfig({ ...editingConfig!, aws: { ...editingConfig!.aws, source_email: v } })} />
      <Text marginTop={1} color="green">Press Enter to save, Esc to cancel.</Text>
    </Box>
  );
};

export const ComposeScreen = ({ setScreen }: { setScreen: (s: Screen) => void }) => {
  const [step, setStep] = useState(0);
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [recipientsStr, setRecipientsStr] = useState('');
  const [filesStr, setFilesStr] = useState('');
  const [sending, setSending] = useState(false);
  const [taskId, setTaskId] = useState('');
  const [status, setStatus] = useState<any>(null);

  useInput((input, key) => {
    if (key.return && step < 3 && !sending) {
      setStep(step + 1);
    } else if (key.return && step === 3 && !sending) {
      handleSend();
    }
  });

  const handleSend = async () => {
    setSending(true);
    const recipients = recipientsStr.split(',').map(s => s.trim()).filter(Boolean);
    const files = filesStr.split(',').map(s => s.trim()).filter(Boolean);
    try {
      const res = await api.sendEmail({ subject, body, recipients, files });
      setTaskId(res.task_id);
      pollStatus(res.task_id);
    } catch (e: any) {
      console.error(e);
      setSending(false);
    }
  };

  const pollStatus = async (id: string) => {
    const s = await api.getSendStatus(id);
    setStatus(s);
    if (s.status === 'completed' || s.status === 'failed' || s.status === 'cancelled') {
      setTimeout(() => setScreen('history'), 2000);
    } else {
      setTimeout(() => pollStatus(id), 1000);
    }
  };

  if (sending) {
    return (
      <Box flexDirection="column">
        <Text bold>Sending Progress</Text>
        <Text>Status: {status?.status}</Text>
        <Text>Sent: {status?.sent_emails} / {status?.total_emails}</Text>
        <Text>Errors: {status?.errors?.length || 0}</Text>
      </Box>
    );
  }

  return (
    <Box flexDirection="column">
      <Text bold>Compose Email</Text>
      <Text>Subject (Step 1/4): {step === 0 ? <Text color="blue">_</Text> : subject}</Text>
      {step === 0 && <TextInput value={subject} onChange={setSubject} />}

      {step > 0 && <Text>Body (Step 2/4): {step === 1 ? <Text color="blue">_</Text> : body}</Text>}
      {step === 1 && <TextInput value={body} onChange={setBody} />}

      {step > 1 && <Text>Recipients (comma separated, Step 3/4): {step === 2 ? <Text color="blue">_</Text> : recipientsStr}</Text>}
      {step === 2 && <TextInput value={recipientsStr} onChange={setRecipientsStr} />}

      {step > 2 && <Text>Files (comma separated, Step 4/4): {step === 3 ? <Text color="blue">_</Text> : filesStr}</Text>}
      {step === 3 && <TextInput value={filesStr} onChange={setFilesStr} />}

      {step === 3 && <Text marginTop={1} color="green">Press Enter to Send</Text>}
    </Box>
  );
};

export const HistoryScreen = ({ setScreen }: { setScreen: (s: Screen) => void }) => {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getHistory().then(data => {
      setHistory(data);
      setLoading(false);
    });
  }, []);

  if (loading) return <Text><Spinner /> Loading history...</Text>;

  const items = history.map(h => ({
    label: `${h.subject} (${h.sent_count} sent) - ${h.last_sent || 'N/A'}`,
    value: h.id
  }));

  if (items.length === 0) items.push({ label: 'No history found', value: 'none' });

  return (
    <Box flexDirection="column">
      <Text bold>Email History</Text>
      // @ts-ignore
      <SelectInput items={items} onSelect={() => {}} />
    </Box>
  );
};

export const SendingScreen = ({ setScreen }: { setScreen: (s: Screen) => void }) => {
  return <Text>Sending...</Text>;
};
