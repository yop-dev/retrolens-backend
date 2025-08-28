-- Add images column to discussions table if it doesn't exist
ALTER TABLE discussions 
ADD COLUMN IF NOT EXISTS images TEXT[] DEFAULT '{}';

-- Comment on the column
COMMENT ON COLUMN discussions.images IS 'Array of image URLs embedded in the discussion';
