-- One-time bootstrap script for a fresh hosted Supabase project.
-- Paste into the Supabase SQL Editor and run once on an empty project.

create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  plan_code text not null default 'A',
  active_user_limit integer not null default 5,
  pending_invite_limit integer not null default 5,
  created_at timestamptz not null default now(),
  constraint organizations_plan_code_check
    check (plan_code in ('A', 'B', 'C')),
  constraint organizations_active_user_limit_check
    check (active_user_limit > 0),
  constraint organizations_pending_invite_limit_check
    check (pending_invite_limit >= 0)
);

create table public.user_profiles (
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

create unique index idx_user_profiles_email_lower
  on public.user_profiles (lower(email));

create table public.organization_memberships (
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

create table public.invitations (
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

create unique index idx_invitations_org_email_pending
  on public.invitations (organization_id, lower(email))
  where status = 'pending';

create table public.audit_logs (
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

create table public.users (
  id uuid primary key,
  organization_id uuid not null references public.organizations(id) on delete cascade,
  email text not null unique,
  display_name text not null default '',
  role text not null default 'member',
  status text not null default 'active',
  created_at timestamptz not null default now(),
  constraint users_role_check check (role in ('admin', 'member')),
  constraint users_status_check check (status in ('active', 'inactive', 'deactivated'))
);

create table public.pipeline_runs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  requested_by uuid not null references public.users(id) on delete restrict,
  parent_run_id uuid references public.pipeline_runs(id) on delete set null,
  status text not null default 'queued',
  run_type text not null,
  source_mode text not null default 'gui_parity',
  started_at timestamptz,
  finished_at timestamptz,
  params_json jsonb not null default '{}'::jsonb,
  summary_json jsonb not null default '{}'::jsonb,
  error_json jsonb not null default '{}'::jsonb,
  progress_stage text not null default '',
  progress_current integer not null default 0,
  progress_total integer not null default 0,
  cancel_requested boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint pipeline_runs_status_check
    check (status in ('queued', 'running', 'success', 'failed', 'cancelled')),
  constraint pipeline_runs_run_type_check
    check (run_type in ('project_tracker', 'tracker_export'))
);

create index idx_pipeline_runs_parent
  on public.pipeline_runs (parent_run_id)
  where parent_run_id is not null;

create index idx_pipeline_runs_org_created_at
  on public.pipeline_runs (organization_id, created_at desc);

create table public.pipeline_logs (
  id bigint generated always as identity primary key,
  run_id uuid not null references public.pipeline_runs(id) on delete cascade,
  organization_id uuid not null references public.organizations(id) on delete cascade,
  level text not null default 'info',
  stage text not null default '',
  message text not null,
  meta_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index idx_pipeline_logs_run_id
  on public.pipeline_logs (run_id, id asc);

create table public.run_artifacts (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.pipeline_runs(id) on delete cascade,
  organization_id uuid not null references public.organizations(id) on delete cascade,
  artifact_type text not null,
  storage_path text not null,
  file_name text not null,
  mime_type text not null default 'application/octet-stream',
  size_bytes bigint not null default 0,
  checksum text not null default '',
  meta_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index idx_run_artifacts_run_created_at
  on public.run_artifacts (run_id, created_at desc);

create table public.project_related_notice_cache (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  project_key text not null,
  snapshot_set_id text not null default 'legacy',
  project_name text not null default '',
  project_search_name text not null default '',
  issuer_name text not null default '',
  status text not null default 'queued',
  source text not null default '',
  algorithm_version integer not null default 0,
  item_count integer not null default 0,
  error text not null default '',
  payload_json jsonb not null default '{}'::jsonb,
  source_run_id uuid references public.pipeline_runs(id) on delete set null,
  generated_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint project_related_notice_cache_status_check
    check (status in ('queued', 'running', 'success', 'failed'))
);

create unique index idx_project_related_notice_cache_org_key
  on public.project_related_notice_cache (organization_id, snapshot_set_id, project_key);

create index idx_project_related_notice_cache_updated_at
  on public.project_related_notice_cache (organization_id, snapshot_set_id, updated_at desc);

create trigger set_project_related_notice_cache_updated_at
before update on public.project_related_notice_cache
for each row
execute function public.set_updated_at();

create table public.related_notice_publications (
  organization_id uuid primary key references public.organizations(id) on delete cascade,
  published_snapshot_set_id text not null,
  source_run_id uuid not null references public.pipeline_runs(id) on delete restrict,
  generated_at timestamptz not null,
  published_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint related_notice_publications_published_snapshot_set_id_check
    check (length(trim(published_snapshot_set_id)) > 0)
);

create index idx_related_notice_publications_snapshot_set_id
  on public.related_notice_publications (published_snapshot_set_id);

drop trigger if exists set_related_notice_publications_updated_at on public.related_notice_publications;
create trigger set_related_notice_publications_updated_at
