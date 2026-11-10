-- Apply with Supabase SQL editor after reviewing target project.
-- This table is intentionally NOT exposed directly to the public Data API.
CREATE TABLE IF NOT EXISTS public.aiwallet_release_interest (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text NOT NULL UNIQUE CHECK (length(email) BETWEEN 5 AND 254),
    name text NOT NULL CHECK (length(name) BETWEEN 2 AND 100),
    plan text NOT NULL CHECK (plan IN ('creator_cloud','studio_workspace')),
    consent boolean NOT NULL CHECK (consent = true),
    source text NOT NULL DEFAULT 'release_lab_v0_1',
    status text NOT NULL DEFAULT 'early_access' CHECK (status IN ('early_access','contacted','opted_out')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.aiwallet_release_interest ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.aiwallet_release_interest FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.aiwallet_release_interest TO service_role;
COMMENT ON TABLE public.aiwallet_release_interest IS 'Opt-in interest only: no payment tokens or customer entitlements';
