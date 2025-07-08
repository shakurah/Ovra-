-- Create marketing_emails table
CREATE TABLE IF NOT EXISTS marketing_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    source_website VARCHAR(255),
    privacy_accepted BOOLEAN DEFAULT FALSE,
    terms_accepted BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create widget_sessions table
CREATE TABLE IF NOT EXISTS widget_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    marketing_email_id UUID REFERENCES marketing_emails(id) ON DELETE CASCADE,
    session_data TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create widget_messages table
CREATE TABLE IF NOT EXISTS widget_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES widget_sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_marketing_emails_email ON marketing_emails(email);
CREATE INDEX IF NOT EXISTS idx_widget_sessions_email_id ON widget_sessions(marketing_email_id);
CREATE INDEX IF NOT EXISTS idx_widget_messages_session_id ON widget_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_widget_messages_created_at ON widget_messages(created_at);