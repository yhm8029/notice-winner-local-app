-- Adds active override metadata to the read-only effective tracker view.
-- This keeps list filtering and API payloads aligned with the base table.

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
