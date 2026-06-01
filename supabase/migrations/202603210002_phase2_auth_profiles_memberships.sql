create table if not exists public.user_profiles (
  id uuid primary key,
  email text not null,
  display_name text not null default '',
  mobile_phone text not null default '',
  office_phone text not null default '',
  account_status text not null default 'active',
  global_role text not null default '',
  last_login_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint user_profiles_account_status_check
    check (account_status in ('active', 'inactive', 'deactivated')),
  constraint user_profiles_global_role_check
    check (global_role in ('', 'platform_admin'))
);

create unique index if not exists idx_user_profiles_email_lower
  on public.user_profiles (lower(email));

create trigger set_user_profiles_updated_at
before update on public.user_profiles
for each row
execute function public.set_updated_at();

create table if not exists public.organization_memberships (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_profile_id uuid not null references public.user_profiles(id) on delete cascade,
  role text not null default 'org_member',
  membership_status text not null default 'active',
  team_name text not null default '',
  job_title text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint organization_memberships_role_check
    check (role in ('org_admin', 'org_member')),
  constraint organization_memberships_status_check
    check (membership_status in ('active', 'inactive', 'deactivated')),
  constraint organization_memberships_org_user_unique
    unique (organization_id, user_profile_id)
);

create index if not exists idx_organization_memberships_user
  on public.organization_memberships (user_profile_id, organization_id);

create index if not exists idx_organization_memberships_org_role
  on public.organization_memberships (organization_id, role, membership_status);

create trigger set_organization_memberships_updated_at
before update on public.organization_memberships
for each row
execute function public.set_updated_at();

create table if not exists public.invitations (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  email text not null,
  role text not null default 'org_member',
  display_name text not null default '',
  team_name text not null default '',
  job_title text not null default '',
  invite_token text not null unique,
  status text not null default 'pending',
  expires_at timestamptz not null,
  accepted_at timestamptz,
  revoked_at timestamptz,
  accepted_user_id uuid references public.user_profiles(id) on delete set null,
  created_by uuid references public.user_profiles(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint invitations_role_check
    check (role in ('org_admin', 'org_member')),
  constraint invitations_status_check
    check (status in ('pending', 'accepted', 'expired', 'revoked'))
);

create unique index if not exists idx_invitations_org_email_pending
  on public.invitations (organization_id, lower(email))
  where status = 'pending';

create index if not exists idx_invitations_org_status_created_at
  on public.invitations (organization_id, status, created_at desc);

create trigger set_invitations_updated_at
before update on public.invitations
for each row
execute function public.set_updated_at();

create table if not exists public.audit_logs (
  id bigint generated always as identity primary key,
  organization_id uuid references public.organizations(id) on delete cascade,
  actor_user_id uuid references public.user_profiles(id) on delete set null,
  actor_membership_id uuid references public.organization_memberships(id) on delete set null,
  event_type text not null,
  target_type text not null default '',
  target_id text not null default '',
  payload_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_audit_logs_org_created_at
  on public.audit_logs (organization_id, created_at desc);

create index if not exists idx_audit_logs_event_created_at
  on public.audit_logs (event_type, created_at desc);

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

insert into public.user_profiles (
  id,
  email,
  display_name,
  account_status,
  global_role,
  created_at,
  updated_at
)
select
  u.id,
  u.email,
  coalesce(u.display_name, ''),
  case
    when lower(coalesce(u.status, 'active')) in ('inactive', 'deactivated') then lower(u.status)
    else 'active'
  end,
  '',
  coalesce(u.created_at, now()),
  coalesce(u.created_at, now())
from public.users u
on conflict (id) do update
set
  email = excluded.email,
  display_name = excluded.display_name,
  account_status = excluded.account_status,
  updated_at = now();

insert into public.organization_memberships (
  organization_id,
  user_profile_id,
  role,
  membership_status,
  created_at,
  updated_at
)
select
  u.organization_id,
  u.id,
  case lower(coalesce(u.role, 'member'))
    when 'admin' then 'org_admin'
    else 'org_member'
  end,
  case
    when lower(coalesce(u.status, 'active')) in ('inactive', 'deactivated') then lower(u.status)
    else 'active'
  end,
  coalesce(u.created_at, now()),
  coalesce(u.created_at, now())
from public.users u
on conflict (organization_id, user_profile_id) do update
set
  role = excluded.role,
  membership_status = excluded.membership_status,
  updated_at = now();

create or replace function public.accept_invitation(
  p_invite_token text,
  p_user_profile_id uuid,
  p_email text,
  p_display_name text default ''
)
returns table (
  invitation_id uuid,
  organization_id uuid,
  organization_name text,
  membership_id uuid,
  user_id uuid,
  role text,
  membership_status text,
  team_name text,
  job_title text
)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_invitation public.invitations%rowtype;
  v_membership public.organization_memberships%rowtype;
  v_org_name text;
  v_now timestamptz := now();
begin
  if trim(coalesce(p_invite_token, '')) = '' then
    raise exception 'invite token is required';
  end if;
  if p_user_profile_id is null then
    raise exception 'user profile id is required';
  end if;
  if trim(coalesce(p_email, '')) = '' then
    raise exception 'email is required';
  end if;

  select *
  into v_invitation
  from public.invitations
  where invite_token = trim(p_invite_token)
  for update;

  if not found then
    raise exception 'invitation not found';
  end if;

  if lower(v_invitation.email) <> lower(trim(p_email)) then
    raise exception 'invitation email does not match the signed-in email';
  end if;

  if v_invitation.status = 'revoked' then
    raise exception 'invitation has been revoked';
  end if;

  if v_invitation.status = 'expired' or v_invitation.expires_at < v_now then
    update public.invitations
    set status = 'expired',
        updated_at = v_now
    where id = v_invitation.id;
    raise exception 'invitation has expired';
  end if;

  update public.user_profiles
  set
    display_name = case
      when coalesce(trim(display_name), '') = '' and trim(coalesce(p_display_name, '')) <> '' then trim(p_display_name)
      else display_name
    end,
    updated_at = v_now
  where id = p_user_profile_id
    and lower(email) = lower(trim(p_email));

  if not found then
    raise exception 'user profile not found for invitation acceptance';
  end if;

  insert into public.organization_memberships (
    organization_id,
    user_profile_id,
    role,
    membership_status,
    team_name,
    job_title
  )
  values (
    v_invitation.organization_id,
    p_user_profile_id,
    v_invitation.role,
    'active',
    v_invitation.team_name,
    v_invitation.job_title
  )
  on conflict (organization_id, user_profile_id) do update
  set
    role = excluded.role,
    membership_status = 'active',
    team_name = case
      when coalesce(public.organization_memberships.team_name, '') = '' then excluded.team_name
      else public.organization_memberships.team_name
    end,
    job_title = case
      when coalesce(public.organization_memberships.job_title, '') = '' then excluded.job_title
      else public.organization_memberships.job_title
    end,
    updated_at = v_now
  returning * into v_membership;

  update public.invitations
  set
    status = 'accepted',
    accepted_at = coalesce(accepted_at, v_now),
    accepted_user_id = p_user_profile_id,
    updated_at = v_now
  where id = v_invitation.id;

  select o.name
  into v_org_name
  from public.organizations o
  where o.id = v_invitation.organization_id;

  return query
  select
    v_invitation.id,
    v_invitation.organization_id,
    coalesce(v_org_name, ''),
    v_membership.id,
    p_user_profile_id,
    v_membership.role,
    v_membership.membership_status,
    v_membership.team_name,
    v_membership.job_title;
end;
$$;
