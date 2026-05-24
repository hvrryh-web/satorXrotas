export type ExportFormat = 'pdf' | 'epub' | 'docx' | 'md' | 'txt' | 'web';

export interface ExportOptions {
  format: ExportFormat;
  pageSize?: 'A4' | 'Letter' | 'US-Trade';
  includeCover?: boolean;
  passwordProtect?: string;
}
