create table public.project_related_notice_cache (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  project_key text not null,
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
  on public.project_related_notice_cache (organization_id, project_key);

create index idx_project_related_notice_cache_updated_at
  on public.project_related_notice_cache (organization_id, updated_at desc);

create trigger set_project_related_notice_cache_updated_at
before update on public.project_related_notice_cache
for each row
execute function public.set_updated_at();
