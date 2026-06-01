create or replace function public.apply_tracker_entry_override(
  p_tracker_entry_id uuid,
  p_field_name text,
  p_new_value text,
  p_actor_user_id uuid default null,
  p_actor_label text default '',
  p_change_source text default 'web'
)
returns public.tracker_entries
language plpgsql
as $$
declare
  v_entry public.tracker_entries%rowtype;
  v_source_value text;
  v_current_override text;
  v_old_effective text;
  v_new_override text;
  v_new_effective text;
  v_override_column text;
begin
  if p_actor_user_id is null and coalesce(p_actor_label, '') = '' then
    raise exception 'actor_user_id or actor_label is required';
  end if;

  if p_change_source not in ('web', 'system', 'import') then
    raise exception 'unsupported change_source: %', p_change_source;
  end if;

  select *
  into v_entry
  from public.tracker_entries
  where id = p_tracker_entry_id
  for update;

  if not found then
    raise exception 'tracker_entry not found: %', p_tracker_entry_id;
  end if;

  case p_field_name
    when 'project_name' then
      v_source_value := v_entry.project_name_source;
      v_current_override := v_entry.project_name_override;
      v_override_column := 'project_name_override';
    when 'gross_area_scale' then
      v_source_value := v_entry.gross_area_scale_source;
      v_current_override := v_entry.gross_area_scale_override;
      v_override_column := 'gross_area_scale_override';
    when 'construction_cost' then
      v_source_value := v_entry.construction_cost_source;
      v_current_override := v_entry.construction_cost_override;
      v_override_column := 'construction_cost_override';
    when 'demand_org_name' then
      v_source_value := v_entry.demand_org_name_source;
      v_current_override := v_entry.demand_org_name_override;
      v_override_column := 'demand_org_name_override';
    when 'demand_contact' then
      v_source_value := v_entry.demand_contact_source;
      v_current_override := v_entry.demand_contact_override;
      v_override_column := 'demand_contact_override';
    when 'client_location' then
      v_source_value := v_entry.client_location_source;
      v_current_override := v_entry.client_location_override;
      v_override_column := 'client_location_override';
    when 'site_location_1' then
      v_source_value := v_entry.site_location_1_source;
      v_current_override := v_entry.site_location_1_override;
      v_override_column := 'site_location_1_override';
    when 'site_location_2' then
      v_source_value := v_entry.site_location_2_source;
      v_current_override := v_entry.site_location_2_override;
      v_override_column := 'site_location_2_override';
    when 'architect_office' then
      v_source_value := v_entry.architect_office_source;
      v_current_override := v_entry.architect_office_override;
      v_override_column := 'architect_office_override';
    when 'construction_start_date' then
      v_source_value := v_entry.construction_start_date_source;
      v_current_override := v_entry.construction_start_date_override;
      v_override_column := 'construction_start_date_override';
    when 'last_checked_date' then
      v_source_value := v_entry.last_checked_date_source;
      v_current_override := v_entry.last_checked_date_override;
      v_override_column := 'last_checked_date_override';
    when 'progress_note' then
      v_source_value := v_entry.progress_note_source;
      v_current_override := v_entry.progress_note_override;
      v_override_column := 'progress_note_override';
    when 'notice_date' then
      v_source_value := v_entry.notice_date_source;
      v_current_override := v_entry.notice_date_override;
      v_override_column := 'notice_date_override';
    when 'manager_name' then
      v_source_value := v_entry.manager_name_source;
      v_current_override := v_entry.manager_name_override;
      v_override_column := 'manager_name_override';
    when 'building_automation_estimated_amount' then
      v_source_value := v_entry.building_automation_estimated_amount_source;
      v_current_override := v_entry.building_automation_estimated_amount_override;
      v_override_column := 'building_automation_estimated_amount_override';
    else
      raise exception 'unsupported field_name: %', p_field_name;
  end case;

  v_old_effective := coalesce(v_current_override, v_source_value);
  v_new_override := p_new_value;

  if v_new_override is not distinct from v_source_value then
    v_new_override := null;
  end if;

  v_new_effective := coalesce(v_new_override, v_source_value);

  if v_current_override is not distinct from v_new_override then
    return v_entry;
  end if;

  execute format(
    'update public.tracker_entries
     set %I = $1,
         last_edited_at = now(),
         last_edited_by = $2,
         last_edited_by_label = $3
     where id = $4
     returning *',
    v_override_column
  )
  into v_entry
  using v_new_override, p_actor_user_id, coalesce(p_actor_label, ''), p_tracker_entry_id;

  if v_old_effective is distinct from v_new_effective then
    insert into public.tracker_entry_audit_logs (
      organization_id,
      tracker_entry_id,
      field_name,
      old_value,
      new_value,
      actor_user_id,
      actor_label,
      change_source
    )
    values (
      v_entry.organization_id,
      v_entry.id,
      p_field_name,
      v_old_effective,
      v_new_effective,
      p_actor_user_id,
      coalesce(p_actor_label, ''),
      p_change_source
    );
  end if;

  return v_entry;
end;
$$;

comment on function public.apply_tracker_entry_override(
  uuid,
  text,
  text,
  uuid,
  text,
  text
) is
'Atomically updates one tracker override field, refreshes last_edited metadata, and inserts one audit log row.';

drop view if exists public.tracker_entries_effective;

create view public.tracker_entries_effective as
with base as (
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
    opening_scheduled_date_source as opening_scheduled_date,
    coalesce(construction_start_date_override, construction_start_date_source) as construction_start_date,
    coalesce(last_checked_date_override, last_checked_date_source) as last_checked_date,
    coalesce(progress_note_override, progress_note_source) as progress_note,
    coalesce(notice_date_override, notice_date_source) as notice_date,
    coalesce(manager_name_override, manager_name_source) as manager_name,
    coalesce(
      building_automation_estimated_amount_override,
      building_automation_estimated_amount_source
    ) as building_automation_estimated_amount,
    array_remove(
      array[
        case when project_name_override is not null then 'project_name' end,
        case when gross_area_scale_override is not null then 'gross_area_scale' end,
        case when construction_cost_override is not null then 'construction_cost' end,
        case when demand_org_name_override is not null then 'demand_org_name' end,
        case when demand_contact_override is not null then 'demand_contact' end,
        case when client_location_override is not null then 'client_location' end,
        case when site_location_1_override is not null then 'site_location_1' end,
        case when site_location_2_override is not null then 'site_location_2' end,
        case when architect_office_override is not null then 'architect_office' end,
        case when construction_start_date_override is not null then 'construction_start_date' end,
        case when last_checked_date_override is not null then 'last_checked_date' end,
        case when progress_note_override is not null then 'progress_note' end,
        case when notice_date_override is not null then 'notice_date' end,
        case when manager_name_override is not null then 'manager_name' end,
        case
          when building_automation_estimated_amount_override is not null
            then 'building_automation_estimated_amount'
        end
      ],
      null
    ) as overridden_fields,
    last_edited_at,
    last_edited_by,
    last_edited_by_label,
    created_at,
    updated_at
  from public.tracker_entries
)
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
  project_name,
  gross_area_scale,
  construction_cost,
  demand_org_name,
  demand_contact,
  client_location,
  site_location_1,
  site_location_2,
  architect_office,
  opening_scheduled_date,
  construction_start_date,
  last_checked_date,
  progress_note,
  notice_date,
  manager_name,
  building_automation_estimated_amount,
  overridden_fields,
  cardinality(overridden_fields) > 0 as has_overrides,
  last_edited_at,
  last_edited_by,
  last_edited_by_label,
  created_at,
  updated_at
from base;

comment on view public.tracker_entries_effective is
'Read-only effective view. Includes overridden_fields and has_overrides for list filtering. Write edits to public.tracker_entries or use an edit RPC inside a single transaction with audit logging.';

create table if not exists public.project_sales_claims (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  project_id uuid not null,
  source_entry_id uuid references public.tracker_entries(id) on delete set null,
  source_run_id uuid references public.pipeline_runs(id) on delete set null,
  project_name text not null default '',
  owner_user_id uuid not null references public.users(id) on delete restrict,
  owner_email text not null default '',
  owner_display_name text not null default '',
  claimed_at timestamptz not null default now(),
  current_owner_assigned_at timestamptz not null default now(),
  released_at timestamptz,
  is_active boolean not null default true,
  claim_status text not null default 'active',
  closed_at timestamptz,
  closed_by uuid references public.users(id) on delete set null,
  sales_note text not null default '',
  sales_note_updated_at timestamptz,
  sales_note_updated_by uuid references public.users(id) on delete set null,
  estimated_amount_text text not null default '',
  estimated_amount_low_krw bigint,
  estimated_amount_high_krw bigint,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint project_sales_claims_status_check
    check (claim_status in ('active', 'won', 'lost'))
);

create unique index if not exists ux_project_sales_claims_active_project
  on public.project_sales_claims (organization_id, project_id)
  where is_active = true;

create index if not exists idx_project_sales_claims_owner
  on public.project_sales_claims (organization_id, owner_user_id, claimed_at desc)
  where is_active = true;

create trigger set_project_sales_claims_updated_at
before update on public.project_sales_claims
for each row
execute function public.set_updated_at();

create table if not exists public.project_sales_claim_events (
  id bigint generated always as identity primary key,
  organization_id uuid not null references public.organizations(id) on delete cascade,
  claim_id uuid not null references public.project_sales_claims(id) on delete cascade,
  project_id uuid not null,
  actor_user_id uuid references public.users(id) on delete set null,
  actor_email text not null default '',
  actor_display_name text not null default '',
  event_type text not null,
  old_value_json jsonb not null default '{}'::jsonb,
  new_value_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint project_sales_claim_events_type_check
    check (event_type in ('claim', 'release', 'force_release', 'note_update', 'transfer', 'close_won', 'close_lost'))
);

create index if not exists idx_project_sales_claim_events_claim
  on public.project_sales_claim_events (claim_id, id desc);

insert into public.organizations (id, name, slug, plan_code, active_user_limit, pending_invite_limit)
values (
  '7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001',
  'Internal Operations',
  'internal-ops',
  'A',
  5,
  5
)
on conflict (id) do update
set
  name = excluded.name,
  slug = excluded.slug,
  plan_code = excluded.plan_code,
  active_user_limit = excluded.active_user_limit,
  pending_invite_limit = excluded.pending_invite_limit;

insert into public.users (id, organization_id, email, display_name, role, status)
