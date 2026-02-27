export interface WorkExperience {
  id: string;
  title: string;
  company: string;
  location: string;
  startDate: string;
  endDate: string;
  type: string;
  description: string;
}

export interface Education {
  id: string;
  school: string;
  degree: string;
  field: string;
  startDate: string;
  endDate: string;
}

export interface UserProfile {
  name: string;
  email: string;
  phone: string;
  summary: string;
  skills: string;
  experience: WorkExperience[];
  education: Education[];
}
