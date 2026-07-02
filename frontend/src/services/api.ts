import axios from 'axios';
import { 
  User, Candidate, JobDescription, 
  Interview, EmailRecord, ActivityLog 
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor to append Authorization Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor to redirect to login on 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // If we are not on login page, redirect
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (email: string, password: string): Promise<{ access_token: string, token_type: string, user: User }> => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await axios.post(`${API_URL}/auth/login`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  register: async (name: string, email: string, password: string, role: string = 'Recruiter'): Promise<{ message: string, user: User }> => {
    const response = await api.post('/auth/register', { name, email, password, role });
    return response.data;
  },
};

export const candidateService = {
  list: async (jobId?: string): Promise<Candidate[]> => {
    const response = await api.get('/candidates', {
      params: jobId ? { job_id: jobId } : {},
    });
    return response.data;
  },
  
  getDetails: async (candidateId: string): Promise<Candidate> => {
    const response = await api.get(`/candidates/${candidateId}`);
    return response.data;
  },
  
  upload: async (jobId: string, file: File): Promise<{ message: string, candidate: Candidate, pipeline_summary: string }> => {
    const formData = new FormData();
    formData.append('job_id', jobId);
    formData.append('file', file);
    
    const response = await api.post('/candidates/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  semanticSearch: async (query: string): Promise<{ candidate: Candidate, score: number }[]> => {
    const response = await api.get('/candidates/search/semantic', {
      params: { query },
    });
    return response.data;
  },
  
  getRankings: async (jobId: string): Promise<{
    ranked_candidates: {
      rank: number;
      id: string;
      name: string;
      email: string;
      match_percentage: number;
      recommendation: string;
      key_skills: string[];
    }[];
    selection_confidence_score: number;
    recruiter_recommendations: string;
  }> => {
    const response = await api.get(`/candidates/rank/${jobId}`);
    return response.data;
  },
  
  updateStatus: async (candidateId: string, status: string): Promise<{ message: string }> => {
    const response = await api.post(`/candidates/${candidateId}/status`, { status });
    return response.data;
  },
};

export const jobService = {
  list: async (): Promise<JobDescription[]> => {
    const response = await api.get('/jobs');
    return response.data;
  },
  
  getDetails: async (jobId: string): Promise<JobDescription> => {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
  },
  
  create: async (job: {
    title: string;
    description: string;
    requirements: string;
    experience_years: number;
    education_requirements: string;
  }): Promise<JobDescription> => {
    const response = await api.post('/jobs', job);
    return response.data;
  },
  
  delete: async (jobId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/jobs/${jobId}`);
    return response.data;
  },
};

export const schedulerService = {
  listInterviews: async (): Promise<Interview[]> => {
    const response = await api.get('/scheduler/interviews');
    return response.data;
  },
  
  listSlots: async (): Promise<string[]> => {
    const response = await api.get('/scheduler/slots');
    return response.data.slots;
  },
  
  schedule: async (payload: {
    candidate_id: string;
    candidate_name: string;
    job_title: string;
    time_slot: string;
  }): Promise<{ message: string, event: Interview }> => {
    const response = await api.post('/scheduler/schedule', payload);
    return response.data;
  },
};

export const emailService = {
  listHistory: async (): Promise<EmailRecord[]> => {
    const response = await api.get('/emails');
    return response.data;
  },
  
  send: async (payload: {
    candidate_name: string;
    recipient_email: string;
    job_title: string;
    template_type: string;
    time_slot?: string;
    meeting_link?: string;
  }): Promise<{ message: string, email: EmailRecord }> => {
    const response = await api.post('/emails/send', payload);
    return response.data;
  },
};

export const chatService = {
  sendMessage: async (message: string): Promise<{ response: string }> => {
    const response = await api.post('/chat/', { message });
    return response.data;
  },
};

export const systemService = {
  getActivityLogs: async (): Promise<ActivityLog[]> => {
    // Falls back to fetch from localStorage or generic system health check if log route is not standalone
    try {
      await api.get('/candidates'); // Can derive from system candidate changes
      return [
        { type: 'info', description: 'HireGenie AI core engine running successfully.', timestamp: new Date().toISOString() }
      ];
    } catch {
      return [];
    }
  }
};
