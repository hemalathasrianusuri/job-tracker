export interface Resume {
  id: string;
  file_url: string;
  original_filename: string;
  is_master: boolean;
  ats_score: number | null;
  created_at: string;
}
