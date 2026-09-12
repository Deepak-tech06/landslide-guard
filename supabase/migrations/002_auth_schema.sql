-- LandslideGuard — Auth & RBAC Schema
-- Creates user roles and Demo Authority Account

-- 1. Create User Roles Table
CREATE TABLE IF NOT EXISTS public.user_roles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('ADMIN', 'AUTHORITY', 'FIELD_TEAM', 'CITIZEN')),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id)
);

-- Enable RLS
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

-- Allow users to read their own role
CREATE POLICY "Users can read own role"
    ON public.user_roles
    FOR SELECT
    USING (auth.uid() = user_id);

-- Allow service role to do everything
CREATE POLICY "Service role has full access"
    ON public.user_roles
    USING (true);

-- 2. Trigger to assign default 'CITIZEN' role on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_roles (user_id, role)
    VALUES (NEW.id, 'CITIZEN');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop trigger if exists so we can recreate it
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Note: Demo accounts must be created manually or via the Supabase Auth API
-- since inserting directly into auth.users requires handling encrypted passwords.
