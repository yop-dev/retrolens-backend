-- RESET AND CREATE ALL TABLES FOR RETROLENS
-- This script drops all existing tables and recreates them with Clerk-compatible user IDs
-- Run this in Supabase SQL Editor to start fresh

-- Step 1: Drop all existing tables and their dependencies
DROP TABLE IF EXISTS public.follows CASCADE;
DROP TABLE IF EXISTS public.likes CASCADE;
DROP TABLE IF EXISTS public.comments CASCADE;
DROP TABLE IF EXISTS public.discussions CASCADE;
DROP TABLE IF EXISTS public.discussion_categories CASCADE;
DROP TABLE IF EXISTS public.camera_images CASCADE;
DROP TABLE IF EXISTS public.cameras CASCADE;
DROP TABLE IF EXISTS public.camera_brands CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;

-- Step 2: Now run the main schema
-- Copy and paste the contents of schema.sql after running the drops above
-- Or run both scripts in sequence

-- Confirmation message
DO $$ 
BEGIN
    RAISE NOTICE 'All tables dropped successfully. Now run schema.sql to recreate them.';
END $$;
