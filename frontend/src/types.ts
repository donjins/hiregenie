export interface User {
  id: string;
  email: string;
  name: string;
  role: 'Recruiter' | 'Admin';
  token?: string;
}

export interface ProjectItem {
  title: string;
  description: string;
}

export interface ExperienceItem {
  role: string;
  duration: string;
  description: string;
}

export interface EducationItem {
  degree: string;
  institution: string;
}

export interface LearningResource {
  skill: string;
  resource_name: string;
  url: string;
}

export interface MatchDetails {
  match_percentage: number;
  strengths: string[];
  weaknesses: string[];
  missing_skills: string[];
  recommendation: 'Hire' | 'Consider' | 'Reject';
  learning_resources: LearningResource[];
  summary: string;
}

export interface HRQuestion {
  question: string;
  intent: string;
}

export interface TechQuestion {
  question: string;
  answer: string;
}

export interface GeneratedQuestions {
  hr_questions: HRQuestion[];
  technical_questions: {
    Beginner: TechQuestion[];
    Intermediate: TechQuestion[];
    Advanced: TechQuestion[];
  };
}

export interface Candidate {
  id: string;
  name: string;
  email: string;
  phone: string;
  skills: string[];
  experience: ExperienceItem[];
  education: EducationItem[];
  certifications: string[];
  projects: ProjectItem[];
  languages: string[];
  status: 'Applied' | 'Shortlisted' | 'Rejected' | 'Hired';
  ats_score?: number;
  job_id: string;
  match_details?: MatchDetails;
  generated_questions?: GeneratedQuestions;
  interview_scheduled: boolean;
  interview_time?: string | null;
}

export interface JobDescription {
  id: string;
  title: string;
  description: string;
  requirements: string;
  experience_years: number;
  education_requirements: string;
  created_at: string;
}

export interface Interview {
  id: string;
  candidate_id: string;
  candidate_name: string;
  job_title: string;
  time_slot: string;
  interviewer: string;
  interviewer_email: string;
  status: string;
  meeting_link: string;
}

export interface EmailRecord {
  id: string;
  candidate_name: string;
  recipient_email: string;
  job_title: string;
  subject: string;
  body: string;
  type: 'invitation' | 'shortlist' | 'rejection' | 'offer';
  status: string;
  sent_at: string;
}

export interface ActivityLog {
  id?: string;
  type: string;
  description: string;
  timestamp: string;
}
