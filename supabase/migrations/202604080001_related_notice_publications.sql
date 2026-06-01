alter table public.project_related_notice_cache
  add column if not exists snapshot_set_id text not null default 'legacy';

update public.project_related_notice_cache
set snapshot_set_id = 'legacy'
where snapshot_set_id is null;

drop index if exists idx_project_related_notice_cache_org_key;

create unique index if not exists idx_project_related_notice_cache_org_snapshot_project
  on public.project_related_notice_cache (organization_id, snapshot_set_id, project_key);

create index if not exists idx_project_related_notice_cache_snapshot_updated_at
  on public.project_related_notice_cache (organization_id, snapshot_set_id, updated_at desc);

create table if not exists public.related_notice_publications (
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

create index if not exists idx_related_notice_publications_published_snapshot_set_id
  on public.related_notice_publications (published_snapshot_set_id);

drop trigger if exists set_related_notice_publications_updated_at on public.related_notice_publications;
create trigger set_related_notice_publications_updated_at
before update on public.related_notice_publications
for each row
execute function public.set_updated_at();
