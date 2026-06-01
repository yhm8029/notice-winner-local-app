create or replace function public.create_invitation(
  p_organization_id uuid,
  p_email text,
  p_role text default 'org_member',
  p_display_name text default '',
  p_team_name text default '',
  p_job_title text default '',
  p_invite_token text default '',
  p_expires_at timestamptz default null,
  p_created_by uuid default null
)
returns public.invitations
language plpgsql
security definer
set search_path = public
as $$
declare
  v_invitation public.invitations%rowtype;
  v_now timestamptz := now();
  v_active_user_limit integer := 5;
  v_pending_invite_limit integer := 5;
  v_active_user_count integer := 0;
  v_pending_invite_count integer := 0;
begin
  if p_organization_id is null then
    raise exception 'organization id is required';
  end if;
  if trim(coalesce(p_email, '')) = '' then
    raise exception 'email is required';
  end if;
  if trim(coalesce(p_invite_token, '')) = '' then
    raise exception 'invite token is required';
  end if;
  if p_expires_at is null then
    raise exception 'expires_at is required';
  end if;
  if p_expires_at <= v_now then
    raise exception 'expires_at must be in the future';
  end if;

  update public.invitations
  set status = 'expired',
      updated_at = v_now
  where organization_id = p_organization_id
    and status = 'pending'
    and expires_at < v_now;

  select
    coalesce(active_user_limit, 5),
    coalesce(pending_invite_limit, 5)
  into
    v_active_user_limit,
    v_pending_invite_limit
  from public.organizations
  where id = p_organization_id
  for update;

  if not found then
    raise exception 'organization not found';
  end if;

  if coalesce(v_active_user_limit, 0) <= 0 then
    v_active_user_limit := 5;
  end if;
  if coalesce(v_pending_invite_limit, -1) < 0 then
    v_pending_invite_limit := 5;
  end if;

  select count(*)
  into v_active_user_count
  from public.organization_memberships m
  join public.user_profiles p on p.id = m.user_profile_id
  where m.organization_id = p_organization_id
    and m.membership_status = 'active'
    and p.account_status = 'active'
    and coalesce(p.global_role, '') <> 'platform_admin';

  if v_active_user_count >= v_active_user_limit then
    raise exception 'active user limit reached for this organization';
  end if;

  select count(*)
  into v_pending_invite_count
  from public.invitations i
  where i.organization_id = p_organization_id
    and i.status = 'pending';

  if v_pending_invite_count >= v_pending_invite_limit then
    raise exception 'pending invite limit reached for this organization';
  end if;

  insert into public.invitations (
    organization_id,
    email,
    role,
    display_name,
    team_name,
    job_title,
    invite_token,
    status,
    expires_at,
    created_by
  )
  values (
    p_organization_id,
    lower(trim(p_email)),
    trim(coalesce(p_role, 'org_member')),
    trim(coalesce(p_display_name, '')),
    trim(coalesce(p_team_name, '')),
    trim(coalesce(p_job_title, '')),
    trim(p_invite_token),
    'pending',
    p_expires_at,
    p_created_by
  )
  returning * into v_invitation;

  return v_invitation;
end;
$$;
