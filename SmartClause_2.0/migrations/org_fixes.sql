-- =============================================================================
-- SmartClause – Organisation Multi-Tenancy Fixes
-- Run this in: Supabase Dashboard → SQL Editor
-- Safe to run multiple times (uses IF NOT EXISTS / OR REPLACE throughout)
-- =============================================================================


-- ---------------------------------------------------------------------------
-- ISSUE 2: Domain auto-join security
-- Adds an opt-in flag so only orgs whose admin explicitly enables it will
-- auto-join users by email domain.
-- ---------------------------------------------------------------------------

ALTER TABLE organizations
    ADD COLUMN IF NOT EXISTS allow_domain_autojoin BOOLEAN NOT NULL DEFAULT false;

COMMENT ON COLUMN organizations.allow_domain_autojoin IS
    'When true, new users whose email domain matches this org are automatically '
    'added as members on sign-up. Must be explicitly enabled by an org admin.';

-- ---------------------------------------------------------------------------
-- ISSUE 7: Missing timestamp columns
-- ---------------------------------------------------------------------------
ALTER TABLE organization_members
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();


-- ---------------------------------------------------------------------------
-- ISSUE 1: Atomic seat check + member insertion (race condition fix)
--
-- Called via: db.client.rpc("add_org_member_atomic", {...})
--
-- The FOR UPDATE on organization_subscriptions acquires a row-level lock,
-- ensuring only one concurrent invite acceptance can succeed when the org is
-- at full capacity. Any concurrent call will wait for the lock and then see
-- the updated seats_used, failing correctly.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION add_org_member_atomic(
    p_organization_id  UUID,
    p_user_id          UUID,
    p_role             TEXT DEFAULT 'member',
    p_invited_by       UUID DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER   -- runs as the function owner, bypasses RLS for the seat check
AS $$
DECLARE
    v_sub           RECORD;
    v_member        RECORD;
    v_seats_used    INT;
BEGIN
    -- Lock the subscription row so concurrent calls serialise here
    SELECT *
    INTO   v_sub
    FROM   organization_subscriptions
    WHERE  organization_id = p_organization_id
      AND  status = 'active'
    FOR UPDATE;

    -- If there is a paid subscription, enforce the seat limit
    IF FOUND THEN
        IF v_sub.seats_used >= v_sub.seats_purchased THEN
            RETURN jsonb_build_object(
                'success', false,
                'error',   'No seats available. Purchase additional seats before inviting more members.'
            );
        END IF;
    END IF;

    -- Upsert the member row (re-activates a suspended member if they rejoin)
    INSERT INTO organization_members (organization_id, user_id, role, status, invited_by)
    VALUES (p_organization_id, p_user_id, p_role, 'active', p_invited_by)
    ON CONFLICT (organization_id, user_id)
    DO UPDATE SET
        role       = EXCLUDED.role,
        status     = 'active',
        invited_by = COALESCE(EXCLUDED.invited_by, organization_members.invited_by),
        updated_at = NOW()
    RETURNING * INTO v_member;

    -- Update seats_used with the authoritative COUNT (not a cached increment)
    IF FOUND AND v_sub IS NOT NULL THEN
        UPDATE organization_subscriptions
        SET    seats_used = (
                   SELECT COUNT(*)
                   FROM   organization_members
                   WHERE  organization_id = p_organization_id
                     AND  status = 'active'
               ),
               updated_at = NOW()
        WHERE  organization_id = p_organization_id;
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'member',  row_to_json(v_member)::JSONB
    );
END;
$$;


-- ---------------------------------------------------------------------------
-- ISSUE 6: Atomic tier upgrade (non-transactional upgrade fix)
--
-- Called via: db.client.rpc("upgrade_org_tier_atomic", {...})
--
-- Both the organizations row and the organization_subscriptions row are
-- updated inside a single PL/pgSQL block, which Postgres executes in one
-- implicit transaction. If either write fails the whole function rolls back.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION upgrade_org_tier_atomic(
    p_organization_id  UUID,
    p_new_tier         TEXT,
    p_seats            INT,
    p_price_per_seat   INT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_period_start  TIMESTAMPTZ := NOW();
    v_period_end    TIMESTAMPTZ := NOW() + INTERVAL '30 days';
    v_sub           RECORD;
BEGIN
    -- 1. Update the organisation's tier
    UPDATE organizations
    SET    subscription_tier = p_new_tier,
           updated_at        = NOW()
    WHERE  id = p_organization_id;

    IF NOT FOUND THEN
        RETURN jsonb_build_object('success', false, 'error', 'Organization not found');
    END IF;

    -- 2. Upsert the subscription row in the same transaction
    INSERT INTO organization_subscriptions
        (organization_id, subscription_tier, seats_purchased, price_per_seat,
         status, current_period_start, current_period_end, next_billing_date)
    VALUES
        (p_organization_id, p_new_tier, p_seats, p_price_per_seat,
         'active', v_period_start, v_period_end, v_period_end)
    ON CONFLICT (organization_id)
    DO UPDATE SET
        subscription_tier    = EXCLUDED.subscription_tier,
        seats_purchased      = EXCLUDED.seats_purchased,
        price_per_seat       = EXCLUDED.price_per_seat,
        status               = 'active',
        current_period_start = EXCLUDED.current_period_start,
        current_period_end   = EXCLUDED.current_period_end,
        next_billing_date    = EXCLUDED.next_billing_date,
        updated_at           = NOW()
    RETURNING * INTO v_sub;

    RETURN jsonb_build_object(
        'success',      true,
        'subscription', row_to_json(v_sub)::JSONB
    );
END;
$$;


-- ---------------------------------------------------------------------------
-- ISSUE 4: Authoritative seats_used trigger (optional but recommended)
--
-- This trigger keeps seats_used in sync whenever organization_members changes,
-- so no application code ever needs to call _update_seats_used() manually.
-- Run the CREATE TRIGGER block only if you want the DB to own this entirely.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION sync_seats_used()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    UPDATE organization_subscriptions
    SET    seats_used = (
               SELECT COUNT(*)
               FROM   organization_members
               WHERE  organization_id = COALESCE(NEW.organization_id, OLD.organization_id)
                 AND  status = 'active'
           ),
           updated_at = NOW()
    WHERE  organization_id = COALESCE(NEW.organization_id, OLD.organization_id);

    RETURN NULL;  -- AFTER trigger; return value is ignored
END;
$$;

-- Drop and recreate so this file is idempotent
DROP TRIGGER IF EXISTS trg_sync_seats_used ON organization_members;

CREATE TRIGGER trg_sync_seats_used
AFTER INSERT OR UPDATE OF status OR DELETE
ON organization_members
FOR EACH ROW
EXECUTE FUNCTION sync_seats_used();


-- ---------------------------------------------------------------------------
-- RLS: grant EXECUTE on the new functions to authenticated users
-- (adjust role name if your project uses a different role)
-- ---------------------------------------------------------------------------

GRANT EXECUTE ON FUNCTION add_org_member_atomic(UUID, UUID, TEXT, UUID)
    TO authenticated;

GRANT EXECUTE ON FUNCTION upgrade_org_tier_atomic(UUID, TEXT, INT, INT)
    TO authenticated;

GRANT EXECUTE ON FUNCTION sync_seats_used()
    TO authenticated;
