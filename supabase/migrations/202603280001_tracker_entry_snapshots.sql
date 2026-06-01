create table if not exists public.tracker_entry_snapshots (
  tracker_entry_id uuid primary key references public.tracker_entries(id) on delete cascade,
  organization_id uuid not null,
  summary_json jsonb not null default '{}'::jsonb,
  detail_json jsonb not null default '{}'::jsonb,
  export_json jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

create index if not exists tracker_entry_snapshots_org_updated_idx
  on public.tracker_entry_snapshots (organization_id, updated_at desc);

create index if not exists tracker_entry_snapshots_updated_idx
  on public.tracker_entry_snapshots (updated_at desc);
