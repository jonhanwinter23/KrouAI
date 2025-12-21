-- ============================================
-- KrouAI Credit System - Supabase Setup
-- Run this in: Supabase Dashboard → SQL Editor
-- ============================================

-- 1. Create user_credits table
CREATE TABLE IF NOT EXISTS user_credits (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    credits INTEGER DEFAULT 0,
    unlocked_books TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Enable Row Level Security
ALTER TABLE user_credits ENABLE ROW LEVEL SECURITY;

-- 3. Policy: Users can read their own credits
CREATE POLICY "Users can view own credits" ON user_credits
    FOR SELECT USING (auth.uid() = user_id);

-- 4. Policy: Users can update their own record (for unlocking books)
CREATE POLICY "Users can update own credits" ON user_credits
    FOR UPDATE USING (auth.uid() = user_id);

-- 5. Policy: Allow insert for authenticated users (auto-create on first login)
CREATE POLICY "Users can insert own credits" ON user_credits
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 6. Function to auto-create credits row on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_credits (user_id, credits, unlocked_books)
    VALUES (NEW.id, 0, '{}');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 7. Trigger to run function on new user signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 8. Function to safely spend credits (prevents negative balance)
CREATE OR REPLACE FUNCTION spend_credits(book_id TEXT, cost INTEGER)
RETURNS JSONB AS $$
DECLARE
    current_credits INTEGER;
    current_books TEXT[];
    result JSONB;
BEGIN
    -- Get current credits and books
    SELECT credits, unlocked_books INTO current_credits, current_books
    FROM user_credits WHERE user_id = auth.uid();
    
    -- Check if already unlocked
    IF book_id = ANY(current_books) THEN
        RETURN jsonb_build_object('success', true, 'message', 'Already unlocked', 'credits', current_credits);
    END IF;
    
    -- Check if enough credits
    IF current_credits < cost THEN
        RETURN jsonb_build_object('success', false, 'message', 'Not enough credits', 'credits', current_credits);
    END IF;
    
    -- Deduct credits and add book
    UPDATE user_credits 
    SET credits = credits - cost,
        unlocked_books = array_append(unlocked_books, book_id),
        updated_at = NOW()
    WHERE user_id = auth.uid();
    
    RETURN jsonb_build_object('success', true, 'message', 'Book unlocked!', 'credits', current_credits - cost);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- PROGRESS TRACKING TABLE
-- ============================================

-- 9. Create reading_progress table
CREATE TABLE IF NOT EXISTS reading_progress (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    book_id TEXT NOT NULL,
    current_chapter INTEGER DEFAULT 0,
    total_chapters INTEGER DEFAULT 1,
    completed BOOLEAN DEFAULT FALSE,
    last_read_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, book_id)
);

-- 10. Enable Row Level Security for progress
ALTER TABLE reading_progress ENABLE ROW LEVEL SECURITY;

-- 11. Policy: Users can read their own progress
CREATE POLICY "Users can view own progress" ON reading_progress
    FOR SELECT USING (auth.uid() = user_id);

-- 12. Policy: Users can insert their own progress
CREATE POLICY "Users can insert own progress" ON reading_progress
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 13. Policy: Users can update their own progress
CREATE POLICY "Users can update own progress" ON reading_progress
    FOR UPDATE USING (auth.uid() = user_id);

-- 14. Function to save reading progress
CREATE OR REPLACE FUNCTION save_progress(
    p_book_id TEXT, 
    p_current_chapter INTEGER, 
    p_total_chapters INTEGER
)
RETURNS JSONB AS $$
DECLARE
    is_completed BOOLEAN;
BEGIN
    is_completed := (p_current_chapter >= p_total_chapters - 1);
    
    INSERT INTO reading_progress (user_id, book_id, current_chapter, total_chapters, completed, last_read_at)
    VALUES (auth.uid(), p_book_id, p_current_chapter, p_total_chapters, is_completed, NOW())
    ON CONFLICT (user_id, book_id) 
    DO UPDATE SET 
        current_chapter = GREATEST(reading_progress.current_chapter, p_current_chapter),
        total_chapters = p_total_chapters,
        completed = is_completed OR reading_progress.completed,
        last_read_at = NOW();
    
    RETURN jsonb_build_object(
        'success', true, 
        'chapter', p_current_chapter, 
        'completed', is_completed
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 15. Function to get all progress for a user
CREATE OR REPLACE FUNCTION get_all_progress()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_object_agg(book_id, jsonb_build_object(
        'current_chapter', current_chapter,
        'total_chapters', total_chapters,
        'completed', completed,
        'percentage', ROUND((current_chapter + 1)::DECIMAL / total_chapters * 100)
    ))
    INTO result
    FROM reading_progress
    WHERE user_id = auth.uid();
    
    RETURN COALESCE(result, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- DONE! Now you can:
-- 1. Add credits to users via Table Editor
-- 2. Users can spend credits to unlock books
-- 3. Track reading progress for each book
-- ============================================

