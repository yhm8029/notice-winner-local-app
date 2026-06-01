-- Editable tracker rows for the web UI.
-- This keeps pipeline output and user overrides separate so reruns do not
-- blindly destroy manual corrections.

create table public.tracker_entries (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  source_run_id uuid not null references public.pipeline_runs(id) on delete restrict,
  source_tracker_run_id uuid references public.pipeline_runs(id) on delete set null,
  entry_key text not null,
  sheet_name text not null default 'Sheet1',
  section_name text not null default '일반관급',
  row_no integer not null default 0,
  source_bid_no text not null default '',
  source_bid_ord text not null default '',
  source_project_name_norm text not null default '',
  project_name_source text not null default '',
  project_name_override text,
  gross_area_scale_source text not null default '',
  gross_area_scale_override text,
  construction_cost_source text not null default '',
  construction_cost_override text,
  demand_org_name_source text not null default '',
  demand_org_name_override text,
  demand_contact_source text not null default '',
  demand_contact_override text,
  client_location_source text not null default '',
  client_location_override text,
  site_location_1_source text not null default '',
  site_location_1_override text,
  site_location_2_source text not null default '',
  site_location_2_override text,
  architect_office_source text not null default '',
  architect_office_override text,
  construction_start_date_source text not null default '',
  construction_start_date_override text,
  last_checked_date_source text not null default '',
  last_checked_date_override text,
  progress_note_source text not null default '',
  progress_note_override text,
  notice_date_source text not null default '',
  notice_date_override text,
  manager_name_source text not null default '',
  manager_name_override text,
  building_automation_estimated_amount_source text not null default '',
  building_automation_estimated_amount_override text,
  last_edited_at timestamptz,
  last_edited_by uuid references public.users(id) on delete set null,
  last_edited_by_label text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint tracker_entries_row_no_check check (row_no >= 0),
  constraint tracker_entries_org_entry_key_unique unique (organization_id, entry_key),
  constraint tracker_entries_last_editor_check
    check (
      (
        last_edited_at is null
        and last_edited_by is null
        and last_edited_by_label = ''
      )
      or (
        last_edited_at is not null
        and (last_edited_by is not null or last_edited_by_label <> '')
      )
    )
);

create index idx_tracker_entries_org_updated_at
  on public.tracker_entries (organization_id, updated_at desc);

create index idx_tracker_entries_source_run
  on public.tracker_entries (source_run_id, row_no asc);

create table public.tracker_entry_audit_logs (
  id bigint generated always as identity primary key,
  organization_id uuid not null references public.organizations(id) on delete cascade,
  tracker_entry_id uuid not null references public.tracker_entries(id) on delete cascade,
  field_name text not null,
  old_value text,
  new_value text,
  actor_user_id uuid references public.users(id) on delete set null,
  actor_label text not null default '',
  change_source text not null default 'web',
  created_at timestamptz not null default now(),
  constraint tracker_entry_audit_logs_actor_check
    check (actor_user_id is not null or actor_label <> ''),
  constraint tracker_entry_audit_logs_change_source_check
    check (change_source in ('web', 'system', 'import')),
  constraint tracker_entry_audit_logs_field_name_check
    check (
      field_name in (
        'project_name',
        'gross_area_scale',
        'construction_cost',
        'demand_org_name',
        'demand_contact',
        'client_location',
        'site_location_1',
        'site_location_2',
        'architect_office',
        'construction_start_date',
        'last_checked_date',
        'progress_note',
        'notice_date',
        'manager_name',
        'building_automation_estimated_amount'
      )
    )
);

create index idx_tracker_entry_audit_logs_entry_created_at
  on public.tracker_entry_audit_logs (tracker_entry_id, created_at desc);

create index idx_tracker_entry_audit_logs_org_created_at
  on public.tracker_entry_audit_logs (organization_id, created_at desc);

create trigger set_tracker_entries_updated_at
before update on public.tracker_entries
for each row
execute function public.set_updated_at();

comment on column public.tracker_entries.entry_key is
'Stable key: lower(source_bid_no) || ''|'' || coalesce(source_bid_ord, '''') || ''|'' || lower(source_project_name_norm). row_no must not be used.';

comment on column public.tracker_entries.source_tracker_run_id is
'The tracker_export child run that last upserted source_* values. tracker_entries are refreshed during tracker_export finalize.';

comment on column public.tracker_entries.row_no is
'Display order only. Do not use as a stable identifier across reruns.';

create view public.tracker_entries_effective as
select
  id,
  organization_id,
  source_run_id,
  source_tracker_run_id,
  entry_key,
  sheet_name,
  section_name,
  row_no,
  source_bid_no,
  source_bid_ord,
  source_project_name_norm,
  coalesce(project_name_override, project_name_source) as project_name,
  coalesce(gross_area_scale_override, gross_area_scale_source) as gross_area_scale,
  coalesce(construction_cost_override, construction_cost_source) as construction_cost,
  coalesce(demand_org_name_override, demand_org_name_source) as demand_org_name,
  coalesce(demand_contact_override, demand_contact_source) as demand_contact,
  coalesce(client_location_override, client_location_source) as client_location,
  coalesce(site_location_1_override, site_location_1_source) as site_location_1,
  coalesce(site_location_2_override, site_location_2_source) as site_location_2,
  coalesce(architect_office_override, architect_office_source) as architect_office,
  coalesce(construction_start_date_override, construction_start_date_source) as construction_start_date,
  coalesce(last_checked_date_override, last_checked_date_source) as last_checked_date,
  coalesce(progress_note_override, progress_note_source) as progress_note,
  coalesce(notice_date_override, notice_date_source) as notice_date,
  coalesce(manager_name_override, manager_name_source) as manager_name,
  coalesce(
    building_automation_estimated_amount_override,
    building_automation_estimated_amount_source
  ) as building_automation_estimated_amount,
  last_edited_at,
  last_edited_by,
  last_edited_by_label,
  created_at,
  updated_at
from public.tracker_entries;

comment on view public.tracker_entries_effective is
'Read-only effective view. Write edits to public.tracker_entries or use an edit RPC inside a single transaction with audit logging.';
