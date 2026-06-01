alter table public.user_profiles
  add column if not exists created_by_user_id uuid references public.user_profiles(id) on delete set null,
  add column if not exists password_setup_mode text not null default 'admin_set',
  add column if not exists force_password_change boolean not null default false;

alter table public.user_profiles
  drop constraint if exists user_profiles_password_setup_mode_check;

alter table public.user_profiles
  add constraint user_profiles_password_setup_mode_check
  check (password_setup_mode in ('admin_set', 'system_generated'));

create or replace view public.organization_member_profiles as
select
  m.id as membership_id,
  m.organization_id,
  o.name as organization_name,
  o.slug as organization_slug,
  m.user_profile_id as user_id,
  p.email,
  p.display_name,
  p.mobile_phone,
  p.office_phone,
  p.account_status,
  p.global_role,
  p.created_by_user_id,
  p.password_setup_mode,
  p.force_password_change,
  m.role as membership_role,
  m.membership_status,
  m.team_name,
  m.job_title,
  p.last_login_at,
  p.created_at as profile_created_at,
  p.updated_at as profile_updated_at,
  m.created_at as membership_created_at,
  m.updated_at as membership_updated_at
from public.organization_memberships m
join public.user_profiles p on p.id = m.user_profile_id
join public.organizations o on o.id = m.organization_id;
