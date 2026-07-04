export interface StackResponse {
  languages: string[];
  frameworks: string[];
  databases: string[];
  cloud: string[];
  devops: string[];
  ai_ml: string[];
  tools: string[];
}

export interface ContactInfo {
  email: string;
  linkedin: string;
  github: string;
  portfolio: string;
}

export interface HireResponse {
  name: string;
  currently_available: boolean;
  status: string;
  preferred_roles: string[];
  employment_types: string[];
  preferred_locations: string[];
  work_authorization: string;
  contact: ContactInfo;
  resume_url: string;
}
