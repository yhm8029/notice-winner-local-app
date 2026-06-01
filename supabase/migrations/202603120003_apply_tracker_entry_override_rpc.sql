-- Atomic tracker edit RPC.
-- Updates one override field, refreshes last_edited metadata, and inserts
-- one audit row in a single transaction.

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
