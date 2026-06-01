-- Phase 1 core schema for the web/SaaS transition.
-- This migration intentionally covers only the approved Phase 1 scope:
--   organizations, users, pipeline_runs, pipeline_logs, run_artifacts, saved_run_presets
-- It deliberately excludes:
--   projects (Phase 2)
--   multi-operator tracking fields such as operator_name / cancel_requested_by

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
  created_at timestamptz not null default now()
);

create table public.users (
  id uuid primary key,
  organization_id uuid not null references public.organizations(id) on delete cascade,
  email text not null unique,
  display_name text not null default '',
  role text not null default 'member',
  created_at timestamptz not null default now(),
  constraint users_role_check check (role in ('admin', 'member'))
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

create table public.saved_run_presets (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  created_by uuid not null references public.users(id) on delete restrict,
  name text not null,
  params_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_saved_run_presets_org_created_at
  on public.saved_run_presets (organization_id, created_at desc);

create trigger set_pipeline_runs_updated_at
before update on public.pipeline_runs
for each row
execute function public.set_updated_at();

create trigger set_saved_run_presets_updated_at
before update on public.saved_run_presets
for each row
execute function public.set_updated_at();
