-- Check current users table structure
-- Run this in Supabase SQL Editor to fix the users table for Clerk integration

-- First, let's check if there's any data we need to preserve
SELECT COUNT(*) as user_count FROM users;

-- Drop existing constraints and modify the users table
-- IMPORTANT: This will work if the table is empty or has minimal test data
-- If you have important data, we'll need a migration strategy

-- Option 1: If the table is empty or only has test data, we can recreate it
-- Uncomment the following lines to drop and recreate the table:

/*
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    id TEXT PRIMARY KEY, -- Changed from UUID to TEXT to store Clerk user IDs
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT,
    bio TEXT DEFAULT '',
    avatar_url TEXT,
    location TEXT,
    expertise_level TEXT DEFAULT 'beginner',
    website_url TEXT,
    instagram_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Add RLS policies if needed
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create a policy that allows users to read all profiles
CREATE POLICY "Public profiles are viewable by everyone" 
ON users FOR SELECT 
USING (true);

-- Create a policy that allows users to update their own profile
CREATE POLICY "Users can update own profile" 
ON users FOR UPDATE 
USING (auth.uid()::text = id);

-- Create a policy for inserting users (typically done by backend)
CREATE POLICY "Enable insert for authenticated users only" 
ON users FOR INSERT 
WITH CHECK (true);
*/

-- Option 2: If you have existing data and want to migrate it
-- This approach adds a clerk_id column and migrates existing data

/*
-- Add clerk_id column if it doesn't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS clerk_id TEXT UNIQUE;

-- If you need to map existing users to Clerk IDs, you would do it here
-- UPDATE users SET clerk_id = 'clerk_user_id_here' WHERE email = 'user@example.com';

-- Create an index on clerk_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_clerk_id ON users(clerk_id);
*/

-- Option 3: Alter existing table to change id type (RECOMMENDED if table is empty)
-- This is the cleanest solution if you don't have data to preserve

-- First check if we need to drop dependent objects
DO $$ 
BEGIN
    -- Drop foreign key constraints from other tables that reference users.id
    -- You may need to add more drops here based on your schema
    
    -- Drop cameras foreign key if exists
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE constraint_name = 'cameras_user_id_fkey' 
               AND table_name = 'cameras') THEN
        ALTER TABLE cameras DROP CONSTRAINT cameras_user_id_fkey;
    END IF;
    
    -- Drop discussions foreign key if exists
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE constraint_name = 'discussions_user_id_fkey' 
               AND table_name = 'discussions') THEN
        ALTER TABLE discussions DROP CONSTRAINT discussions_user_id_fkey;
    END IF;
    
    -- Drop follows foreign keys if exist
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE constraint_name = 'follows_follower_id_fkey' 
               AND table_name = 'follows') THEN
        ALTER TABLE follows DROP CONSTRAINT follows_follower_id_fkey;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE constraint_name = 'follows_following_id_fkey' 
               AND table_name = 'follows') THEN
        ALTER TABLE follows DROP CONSTRAINT follows_following_id_fkey;
    END IF;
END $$;

-- Now alter the users table id column type
ALTER TABLE users ALTER COLUMN id TYPE TEXT USING id::TEXT;

-- Recreate foreign key constraints with the new TEXT type
DO $$
BEGIN
    -- Recreate cameras foreign key
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cameras') THEN
        ALTER TABLE cameras ALTER COLUMN user_id TYPE TEXT USING user_id::TEXT;
        ALTER TABLE cameras 
        ADD CONSTRAINT cameras_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
    
    -- Recreate discussions foreign key
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'discussions') THEN
        ALTER TABLE discussions ALTER COLUMN user_id TYPE TEXT USING user_id::TEXT;
        ALTER TABLE discussions 
        ADD CONSTRAINT discussions_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
    
    -- Recreate follows foreign keys
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'follows') THEN
        ALTER TABLE follows ALTER COLUMN follower_id TYPE TEXT USING follower_id::TEXT;
        ALTER TABLE follows ALTER COLUMN following_id TYPE TEXT USING following_id::TEXT;
        ALTER TABLE follows 
        ADD CONSTRAINT follows_follower_id_fkey 
        FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE;
        ALTER TABLE follows 
        ADD CONSTRAINT follows_following_id_fkey 
        FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Verify the changes
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
AND table_schema = 'public'
ORDER BY ordinal_position;

-- Check if any users exist
SELECT id, email, username FROM users LIMIT 5;
