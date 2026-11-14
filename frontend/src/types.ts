export type EmotionName = "joy" | "sadness" | "calm" | "energy" | "romance" | "anxiety";

export type Track = {
  id: string;
  title: string;
  artist: string;
  genre: string;
  description: string;
  emotion_scores: Record<EmotionName, number>;
  listening_url: string | null;
  score: number;
  score_breakdown: {
    semantic: number | null;
    lexical: number | null;
    emotion: number | null;
    genre: number | null;
  } | null;
  is_favorite: boolean;
};

export type SearchResponse = {
  query: string;
  mode: "hybrid" | "lexical_fallback";
  emotion_mode: "rubert_multi_label" | "lexicon";
  embedding_model: string | null;
  notice: string | null;
  results: Track[];
};

export type User = {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  user: User;
};

export type SearchHistoryEntry = {
  id: string;
  query: string;
  created_at: string;
};
