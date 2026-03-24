-- =============================================================================
-- SmartClause – Team Granular Document Access Updates
-- Run this in: Supabase Dashboard → SQL Editor
-- =============================================================================

-- 1. Add organization_id to matters to link them to the broader team
ALTER TABLE matters 
    ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;

-- 2. Populate existing matters with their creator's active organization ID (if any)
UPDATE matters m
SET organization_id = om.organization_id
FROM organization_members om
WHERE m.user_id = om.user_id 
  AND om.status = 'active'
  AND m.organization_id IS NULL;

-- 3. Create the matter_access table to track granular permissions 
CREATE TABLE IF NOT EXISTS matter_access (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    matter_id UUID NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    access_level TEXT NOT NULL DEFAULT 'edit' CHECK (access_level IN ('view', 'edit')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(matter_id, user_id)
);

-- 4. Enable Row Level Security (RLS) on matter_access (Standard Supabase Practice)
ALTER TABLE matter_access ENABLE ROW LEVEL SECURITY;

-- 5. Add last_edited_by directly to documents table for easy reading
ALTER TABLE documents 
    ADD COLUMN IF NOT EXISTS last_edited_by UUID REFERENCES auth.users(id) ON DELETE SET NULL;

-- 6. Populate last_edited_by for existing documents from their latest versions
UPDATE documents d
SET last_edited_by = v.created_by
FROM document_versions v
WHERE v.document_id = d.id 
  AND d.last_edited_by IS NULL
  AND v.version_number = (
      SELECT MAX(version_number) FROM document_versions dv WHERE dv.document_id = d.id
  );
