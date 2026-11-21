ALTER TABLE public.patient_sessions
ADD COLUMN IF NOT EXISTS draft_profile JSONB;
