create table if not exists public.backfill_conflicts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  tracker_entry_id uuid not null references public.tracker_entries(id) on delete cascade,
  field_name text not null,
  current_value text not null default '',
  candidate_value text not null default '',
  current_value_norm text,
  candidate_value_norm text,
  reason_code text not null,
  source_kind text not null,
  source_ref text,
  source_run_id uuid references public.pipeline_runs(id) on delete set null,
  extractor_version text,
  detected_at timestamptz not null default now(),
  resolved_at timestamptz,
  resolution text,
  conflict_key text not null,
  constraint backfill_conflicts_field_name_check
    check (field_name in ('gross_area_scale', 'construction_cost', 'demand_contact')),
  constraint backfill_conflicts_source_kind_check
    check (source_kind in ('tracker_export', 'backfill')),
  constraint backfill_conflicts_resolution_check
    check (resolution in ('kept_current', 'applied_manually', 'applied_via_backfill', 'dismissed') or resolution is null)
);

create unique index if not exists ux_backfill_conflicts_conflict_key
  on public.backfill_conflicts (conflict_key);

create index if not exists idx_backfill_conflicts_open
  on public.backfill_conflicts (organization_id, detected_at desc)
  where resolved_at is null;

create index if not exists idx_backfill_conflicts_entry_field
  on public.backfill_conflicts (tracker_entry_id, field_name, detected_at desc);
