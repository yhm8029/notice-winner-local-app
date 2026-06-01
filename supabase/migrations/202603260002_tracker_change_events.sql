create table if not exists public.tracker_change_events (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  tracker_entry_id uuid not null references public.tracker_entries(id) on delete cascade,
  event_type text not null,
  field_name text,
  old_value text not null default '',
  new_value text not null default '',
  old_value_norm text,
  new_value_norm text,
  source_run_id uuid references public.pipeline_runs(id) on delete set null,
  source_kind text not null,
  source_ref text,
  extractor_version text,
  reason_code text,
  batch_key text,
  dedupe_key text not null,
  is_silent boolean not null default false,
  created_at timestamptz not null default now(),
  is_read boolean not null default false,
  read_at timestamptz,
  constraint tracker_change_events_type_check
    check (event_type in (
      'related_notice_added',
      'field_filled',
      'field_updated_safe',
      'field_conflict_detected',
      'manual_updated'
    )),
  constraint tracker_change_events_source_kind_check
    check (source_kind in ('tracker_export', 'backfill', 'manual'))
);

create unique index if not exists ux_tracker_change_events_dedupe_key
  on public.tracker_change_events (dedupe_key);

create index if not exists idx_tracker_change_events_unread
  on public.tracker_change_events (organization_id, is_read, is_silent, created_at desc);

create index if not exists idx_tracker_change_events_entry_created
  on public.tracker_change_events (tracker_entry_id, created_at desc);
