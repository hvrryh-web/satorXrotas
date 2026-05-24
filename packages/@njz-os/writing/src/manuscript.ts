export type ChapterStatus = 'outline' | 'draft' | 'editing' | 'complete' | 'archived';

export interface Chapter {
  id: string;
  index: number;
  title: string;
  status: ChapterStatus;
  wordCount: number;
  content: string;
  goalWords?: number;
}

export interface Manuscript {
  id: string;
  title: string;
  subtitle?: string;
  genre?: string;
  targetWords: number;
  deadline?: string;
  chapters: Chapter[];
  characters?: { id: string; name: string; description?: string }[];
  places?: { id: string; name: string; description?: string }[];
}
