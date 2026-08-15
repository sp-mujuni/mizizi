/** TypeScript types mirroring the Mizizi API schemas. */

export type ObjectType =
  | "story"
  | "song"
  | "riddle"
  | "proverb"
  | "poem"
  | "chant"
  | "oral_history"
  | "lullaby"
  | "tongue_twister"
  | "tradition"
  | "ceremony"
  | "game"
  | "recipe"
  | "personal_memory"
  | "other";

export type ObjectStatus =
  | "draft"
  | "processing"
  | "review"
  | "verified"
  | "published"
  | "restricted"
  | "withdrawn"
  | "archived";

export type VerificationStatus =
  | "unverified"
  | "ai_processed"
  | "human_reviewed"
  | "community_verified"
  | "expert_verified";

export interface Language {
  id: string;
  name: string;
  iso_639_3?: string;
  glottocode?: string;
  description?: string;
}

export interface Community {
  id: string;
  name: string;
  country?: string;
  region?: string;
  description?: string;
}

export interface Place {
  id: string;
  name: string;
  country?: string;
  region?: string;
  district?: string;
  latitude?: number;
  longitude?: number;
}

export interface Contributor {
  id: string;
  display_name?: string;
  anonymous: boolean;
  role?: string;
}

export interface MediaAsset {
  id: string;
  media_type: string;
  mime_type?: string;
  original_filename?: string;
  storage_key: string;
  file_size?: number;
  duration_seconds?: number;
  sha256_checksum: string;
  is_original: boolean;
  created_at: string;
}

export interface Transcription {
  id: string;
  language_id?: string;
  language?: Language | null;
  text: string;
  model_name?: string;
  model_version?: string;
  confidence?: number;
  version: number;
  verification_status: string;
  created_by?: string;
  created_at: string;
}

export interface Translation {
  id: string;
  source_transcription_id?: string;
  source_language?: Language | null;
  target_language?: Language | null;
  text: string;
  model_name?: string;
  verification_status: string;
  created_at: string;
}

export interface Permission {
  id: string;
  preservation: boolean;
  public_access: boolean;
  educational_use: boolean;
  ai_analysis: boolean;
  ai_training: boolean;
  derivative_work: boolean;
  commercial_use: boolean;
  voice_cloning: boolean;
}

export interface ProvenanceEvent {
  id: string;
  event_type: string;
  actor?: string;
  description?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface Derivative {
  id: string;
  derivative_type: string;
  title?: string;
  content?: string;
  model_name?: string;
  human_reviewed: boolean;
  created_at: string;
}

export interface CulturalObject {
  id: string;
  object_code: string;
  object_type: string;
  title?: string;
  description?: string;
  status: string;
  visibility: string;
  verification_status: string;
  version: number;
  created_at: string;
  updated_at: string;
  original_language?: Language | null;
  community?: Community | null;
  place?: Place | null;
  contributor?: Contributor | null;
  media_assets: MediaAsset[];
  transcriptions: Transcription[];
  translations: Translation[];
  cultural_context?: { genre?: string; themes?: string; audience?: string } | null;
  permissions: Permission[];
  consents: { id: string; consenting_party: string; consent_type: string }[];
  provenance_events: ProvenanceEvent[];
  derivatives: Derivative[];
  tags: { id: string; name: string }[];
}

export interface PaginatedObjects {
  items: CulturalObject[];
  total: number;
  limit: number;
  offset: number;
}

export interface SearchResponse {
  query: string;
  mode: string;
  results: CulturalObject[];
  total: number;
}

export interface PublishRequirement {
  requirement: string;
  label: string;
  satisfied: boolean;
}

export interface PublishCheck {
  object_id: string;
  requirements: PublishRequirement[];
}

export interface CreatedObject {
  id: string;
  object_code: string;
  status: string;
  visibility: string;
  creator_key: string;
}

export interface UserProfileBrief {
  id: string;
  name: string;
}

export interface User {
  id: string;
  email: string;
  display_name?: string | null;
  role: string;
  languages: UserProfileBrief[];
  places: UserProfileBrief[];
  communities: UserProfileBrief[];
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ReviewerApplication {
  id: string;
  user_id: string;
  user_email: string;
  user_display_name?: string | null;
  statement: string;
  status: string;
  decided_at?: string | null;
  created_at: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  display_name?: string;
  language_ids: string[];
  place_ids: string[];
  community_ids: string[];
}