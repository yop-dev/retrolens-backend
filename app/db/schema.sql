-- RetroLens Database Schema for Supabase
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if you're resetting (uncomment if needed)
-- DROP TABLE IF EXISTS public.follows CASCADE;
-- DROP TABLE IF EXISTS public.likes CASCADE;
-- DROP TABLE IF EXISTS public.comments CASCADE;
-- DROP TABLE IF EXISTS public.discussions CASCADE;
-- DROP TABLE IF EXISTS public.discussion_categories CASCADE;
-- DROP TABLE IF EXISTS public.camera_images CASCADE;
-- DROP TABLE IF EXISTS public.cameras CASCADE;
-- DROP TABLE IF EXISTS public.camera_brands CASCADE;
-- DROP TABLE IF EXISTS public.users CASCADE;

-- Users table (compatible with Clerk user IDs)
CREATE TABLE IF NOT EXISTS public.users (
    id VARCHAR(255) PRIMARY KEY,  -- Clerk user ID
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    display_name VARCHAR(100),
    bio TEXT,
    avatar_url TEXT,
    location VARCHAR(100),
    expertise_level VARCHAR(20) CHECK (expertise_level IN ('beginner', 'intermediate', 'expert')),
    website_url TEXT,
    instagram_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Camera brands table
CREATE TABLE IF NOT EXISTS public.camera_brands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Insert common camera brands
INSERT INTO public.camera_brands (name) VALUES 
    ('Leica'), ('Hasselblad'), ('Canon'), ('Nikon'), ('Pentax'),
    ('Minolta'), ('Olympus'), ('Rolleiflex'), ('Yashica'), ('Contax'),
    ('Mamiya'), ('Fujifilm'), ('Kodak'), ('Polaroid'), ('Zeiss')
ON CONFLICT (name) DO NOTHING;

-- Cameras table
CREATE TABLE IF NOT EXISTS public.cameras (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    brand_id UUID REFERENCES public.camera_brands(id),
    brand_name VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    year VARCHAR(50),
    camera_type VARCHAR(50),
    film_format VARCHAR(50),
    condition VARCHAR(20) CHECK (condition IN ('mint', 'excellent', 'good', 'fair', 'poor', 'for_parts')),
    acquisition_story TEXT,
    technical_specs JSONB,
    market_value_min DECIMAL(10, 2),
    market_value_max DECIMAL(10, 2),
    is_for_sale BOOLEAN DEFAULT FALSE,
    is_for_trade BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT TRUE,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Camera images table
CREATE TABLE IF NOT EXISTS public.camera_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_id UUID NOT NULL REFERENCES public.cameras(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    thumbnail_url TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Discussion categories table
CREATE TABLE IF NOT EXISTS public.discussion_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Insert default discussion categories
INSERT INTO public.discussion_categories (name, description, icon, display_order) VALUES 
    ('General Discussion', 'General topics about vintage cameras', '💬', 1),
    ('Camera Reviews', 'Reviews and recommendations', '⭐', 2),
    ('Restoration & Repair', 'Tips and help for camera restoration', '🔧', 3),
    ('Film & Technique', 'Film stocks, development, and shooting techniques', '🎞️', 4),
    ('Market & Trading', 'Buy, sell, trade, and price discussions', '💰', 5),
    ('Show & Tell', 'Share your latest finds and collections', '📸', 6)
ON CONFLICT (name) DO NOTHING;

-- Discussions table
CREATE TABLE IF NOT EXISTS public.discussions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    category_id UUID REFERENCES public.discussion_categories(id),
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    tags TEXT[],
    is_pinned BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Comments table
CREATE TABLE IF NOT EXISTS public.comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    discussion_id UUID REFERENCES public.discussions(id) ON DELETE CASCADE,
    camera_id UUID REFERENCES public.cameras(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES public.comments(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    is_edited BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    CONSTRAINT comment_target CHECK (
        (discussion_id IS NOT NULL AND camera_id IS NULL) OR 
        (discussion_id IS NULL AND camera_id IS NOT NULL)
    )
);

-- Likes table
CREATE TABLE IF NOT EXISTS public.likes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    discussion_id UUID REFERENCES public.discussions(id) ON DELETE CASCADE,
    comment_id UUID REFERENCES public.comments(id) ON DELETE CASCADE,
    camera_id UUID REFERENCES public.cameras(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    CONSTRAINT unique_user_like UNIQUE (user_id, discussion_id, comment_id, camera_id),
    CONSTRAINT like_target CHECK (
        (discussion_id IS NOT NULL AND comment_id IS NULL AND camera_id IS NULL) OR 
        (discussion_id IS NULL AND comment_id IS NOT NULL AND camera_id IS NULL) OR
        (discussion_id IS NULL AND comment_id IS NULL AND camera_id IS NOT NULL)
    )
);

-- Follows table
CREATE TABLE IF NOT EXISTS public.follows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    follower_id VARCHAR(255) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    following_id VARCHAR(255) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    CONSTRAINT unique_follow UNIQUE (follower_id, following_id),
    CONSTRAINT no_self_follow CHECK (follower_id != following_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_cameras_user_id ON public.cameras(user_id);
CREATE INDEX IF NOT EXISTS idx_cameras_brand_id ON public.cameras(brand_id);
CREATE INDEX IF NOT EXISTS idx_camera_images_camera_id ON public.camera_images(camera_id);
CREATE INDEX IF NOT EXISTS idx_discussions_user_id ON public.discussions(user_id);
CREATE INDEX IF NOT EXISTS idx_discussions_category_id ON public.discussions(category_id);
CREATE INDEX IF NOT EXISTS idx_comments_discussion_id ON public.comments(discussion_id);
CREATE INDEX IF NOT EXISTS idx_comments_camera_id ON public.comments(camera_id);
CREATE INDEX IF NOT EXISTS idx_comments_user_id ON public.comments(user_id);
CREATE INDEX IF NOT EXISTS idx_likes_user_id ON public.likes(user_id);
CREATE INDEX IF NOT EXISTS idx_follows_follower_id ON public.follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_follows_following_id ON public.follows(following_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cameras_updated_at BEFORE UPDATE ON public.cameras
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_discussions_updated_at BEFORE UPDATE ON public.discussions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_comments_updated_at BEFORE UPDATE ON public.comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) Policies
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cameras ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.camera_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.discussions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.follows ENABLE ROW LEVEL SECURITY;

-- Users policies (simplified for Clerk development)
CREATE POLICY "Users can view all profiles" ON public.users
    FOR SELECT USING (true);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (true);  -- Simplified for development

CREATE POLICY "Users can insert profile" ON public.users
    FOR INSERT WITH CHECK (true);  -- Allow Clerk user creation

-- Cameras policies (simplified for development)
CREATE POLICY "Public cameras are viewable by all" ON public.cameras
    FOR SELECT USING (true);

CREATE POLICY "Users can create own cameras" ON public.cameras
    FOR INSERT WITH CHECK (true);  -- Simplified for development

CREATE POLICY "Users can update own cameras" ON public.cameras
    FOR UPDATE USING (true);  -- Simplified for development

CREATE POLICY "Users can delete own cameras" ON public.cameras
    FOR DELETE USING (true);  -- Simplified for development

-- Note: In production, you would check against the Clerk user ID from your backend
-- These permissive policies are for development only
