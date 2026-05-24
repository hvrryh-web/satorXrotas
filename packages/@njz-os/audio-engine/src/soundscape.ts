export type SoundscapeCategory = 'focus' | 'relax' | 'sleep' | 'meditate';
export type SoundscapeTheme = 'nature' | 'urban' | 'cosmic' | 'minimal' | 'instrumental';

export interface Soundscape {
  id: string;
  title: string;
  category: SoundscapeCategory;
  theme: SoundscapeTheme;
  durationMs: number;
  stems: string[];
  isPremium: boolean;
}
