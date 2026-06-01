-- Phase 1 bootstrap seed.
-- This file creates the single internal organization/user pair that the
-- approved Phase 1 design assumes for requested_by / created_by.

begin;

insert into public.organizations (
  id,
  name,
  slug,
  plan_code,
  active_user_limit,
  pending_invite_limit
)
values (
  '7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001',
  'Internal Operations',
  'internal-ops',
  'A',
  5,
  5
)
on conflict (id) do update
set
  name = excluded.name,
  slug = excluded.slug,
  plan_code = excluded.plan_code,
  active_user_limit = excluded.active_user_limit,
  pending_invite_limit = excluded.pending_invite_limit;

insert into public.users (
  id,
  organization_id,
  email,
  display_name,
  role
)
values (
  '8e9d2b94-4c95-4e2b-9be8-2be1d96e1001',
  '7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001',
  'internal-user@local.internal',
  'Internal User',
  'member'
)
on conflict (id) do update
set
  organization_id = excluded.organization_id,
  email = excluded.email,
  display_name = excluded.display_name,
  role = excluded.role;

insert into public.user_profiles (
  id,
  email,
  display_name,
  account_status,
  global_role
)
values (
  '8e9d2b94-4c95-4e2b-9be8-2be1d96e1001',
  'internal-user@local.internal',
  'Internal User',
  'active',
  ''
)
on conflict (id) do update
set
  email = excluded.email,
  display_name = excluded.display_name,
  account_status = excluded.account_status,
  global_role = excluded.global_role;

insert into public.organization_memberships (
  organization_id,
  user_profile_id,
  role,
  membership_status
)
values (
  '7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001',
  '8e9d2b94-4c95-4e2b-9be8-2be1d96e1001',
  'org_member',
  'active'
)
on conflict (organization_id, user_profile_id) do update
set
  role = excluded.role,
  membership_status = excluded.membership_status;

commit;
