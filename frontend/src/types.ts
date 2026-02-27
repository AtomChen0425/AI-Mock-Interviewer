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
export interface ProjectExperience {
  id: string;
  title: string;
  startDate: string;
  endDate: string;
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
  workexperience: WorkExperience[];
  projectexperience: ProjectExperience[];
  education: Education[];
}
export interface InterviewRecord {
  id: string;
  date: string;
  jobDescription: string;
  type: string;
  resumeContext: string;
  chatHistory: { role: string; text: string }[];
  feedbackHtml?: string;
}
