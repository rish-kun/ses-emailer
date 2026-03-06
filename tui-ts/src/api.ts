import axios from 'axios';

const PORT = process.env.API_PORT || 8000;
const TOKEN = process.env.API_TOKEN || '';

export const apiClient = axios.create({
  baseURL: `http://127.0.0.1:${PORT}`,
  headers: {
    Authorization: `Bearer ${TOKEN}`,
  },
});

export interface AppConfig {
  aws: {
    access_key_id: string;
    secret_access_key: string;
    region: string;
    source_email: string;
  };
  sender: {
    sender_name: string;
    reply_to: string;
    default_to: string;
  };
  batch: {
    batch_size: number;
    delay_seconds: number;
    use_bcc: boolean;
  };
  files_directory: string;
  data_directory: string;
  last_excel_path: string;
  last_excel_column: number;
  theme: string;
  test_recipients: string[];
}

export interface Profile {
  id: string;
  name: string;
  config: AppConfig;
}

export const api = {
  getProfiles: async () => {
    const res = await apiClient.get<Profile[]>('/profiles');
    return res.data;
  },
  getActiveProfile: async () => {
    const res = await apiClient.get<Profile>('/profiles/active');
    return res.data;
  },
  setActiveProfile: async (id: string) => {
    await apiClient.post(`/profiles/active/${id}`);
  },
  createProfile: async (name: string, config?: AppConfig) => {
    const res = await apiClient.post<Profile>('/profiles', config, { params: { name } });
    return res.data;
  },
  updateProfile: async (id: string, name?: string, config?: AppConfig) => {
    const res = await apiClient.put<Profile>(`/profiles/${id}`, config, { params: { name } });
    return res.data;
  },
  deleteProfile: async (id: string) => {
    await apiClient.delete(`/profiles/${id}`);
  },
  sendEmail: async (data: { subject: string; body: string; recipients: string[]; files?: string[]; email_type?: string }) => {
    const res = await apiClient.post<{ task_id: string; message: string }>('/send', data);
    return res.data;
  },
  getSendStatus: async (taskId: string) => {
    const res = await apiClient.get(`/send/status/${taskId}`);
    return res.data;
  },
  cancelSend: async (taskId: string) => {
    await apiClient.post(`/send/cancel/${taskId}`);
  },
  getHistory: async () => {
    const res = await apiClient.get('/history');
    return res.data;
  },
  getFiles: async () => {
    const res = await apiClient.get<{files: string[]}>('/files');
    return res.data;
  }
};
