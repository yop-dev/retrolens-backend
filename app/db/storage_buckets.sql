-- Supabase Storage Buckets Configuration
-- Run this in your Supabase SQL Editor after creating the tables

-- Create storage buckets
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES 
    ('camera-images', 'camera-images', true, 5242880, ARRAY['image/jpeg', 'image/png', 'image/webp']),
    ('user-avatars', 'user-avatars', true, 2097152, ARRAY['image/jpeg', 'image/png', 'image/webp'])
ON CONFLICT (id) DO UPDATE
SET 
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- Storage policies for camera-images bucket
CREATE POLICY "Anyone can view camera images" ON storage.objects
    FOR SELECT USING (bucket_id = 'camera-images');

CREATE POLICY "Authenticated users can upload camera images" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'camera-images' 
        AND auth.role() = 'authenticated'
    );

CREATE POLICY "Users can update their own camera images" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'camera-images' 
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can delete their own camera images" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'camera-images' 
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

-- Storage policies for user-avatars bucket
CREATE POLICY "Anyone can view avatars" ON storage.objects
    FOR SELECT USING (bucket_id = 'user-avatars');

CREATE POLICY "Users can upload their own avatar" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'user-avatars' 
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can update their own avatar" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'user-avatars' 
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can delete their own avatar" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'user-avatars' 
        AND auth.uid()::text = (storage.foldername(name))[1]
    );
