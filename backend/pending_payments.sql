-- Add this table to your Supabase database for tracking pending Bakong payments

CREATE TABLE IF NOT EXISTS pending_payments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    bill_number TEXT NOT NULL UNIQUE,
    md5_hash TEXT NOT NULL UNIQUE,
    credits INTEGER NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'KHR',
    status TEXT NOT NULL DEFAULT 'pending',
    qr_string TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster lookups
CREATE INDEX idx_pending_payments_md5 ON pending_payments(md5_hash);
CREATE INDEX idx_pending_payments_user ON pending_payments(user_id);
CREATE INDEX idx_pending_payments_status ON pending_payments(status);

-- Enable RLS
ALTER TABLE pending_payments ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only view their own pending payments
CREATE POLICY "Users can view own pending payments" ON pending_payments
    FOR SELECT USING (auth.uid() = user_id);

