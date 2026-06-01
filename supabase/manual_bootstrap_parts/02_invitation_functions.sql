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

create or replace function public.accept_invitation(
  p_invite_token text,
  p_user_profile_id uuid,
  p_email text,
  p_display_name text default ''
)
returns table (
  invitation_id uuid,
  organization_id uuid,
  organization_name text,
  membership_id uuid,
  user_id uuid,
  role text,
  membership_status text,
  team_name text,
  job_title text
)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_invitation public.invitations%rowtype;
  v_membership public.organization_memberships%rowtype;
  v_org_name text;
  v_now timestamptz := now();
  v_user_global_role text := '';
  v_active_user_limit integer := 5;
  v_active_user_count integer := 0;
  v_existing_membership_active boolean := false;
begin
  if trim(coalesce(p_invite_token, '')) = '' then
    raise exception 'invite token is required';
  end if;
  if p_user_profile_id is null then
    raise exception 'user profile id is required';
  end if;
  if trim(coalesce(p_email, '')) = '' then
    raise exception 'email is required';
  end if;

  select *
  into v_invitation
  from public.invitations
  where invite_token = trim(p_invite_token)
  for update;

  if not found then
    raise exception 'invitation not found';
  end if;

  if lower(v_invitation.email) <> lower(trim(p_email)) then
    raise exception 'invitation email does not match the signed-in email';
  end if;

  if v_invitation.status = 'accepted' then
    if v_invitation.accepted_user_id is not null and v_invitation.accepted_user_id <> p_user_profile_id then
      raise exception 'invitation already belongs to another account';
    end if;

    select m.*
    into v_membership
    from public.organization_memberships m
    where m.organization_id = v_invitation.organization_id
      and m.user_profile_id = p_user_profile_id
      and m.membership_status = 'active'
    for update;

    if found then
      select o.name
      into v_org_name
      from public.organizations o
      where o.id = v_invitation.organization_id;

      return query
      select
        v_invitation.id,
        v_invitation.organization_id,
        coalesce(v_org_name, ''),
        v_membership.id,
        p_user_profile_id,
        v_membership.role,
        v_membership.membership_status,
        v_membership.team_name,
        v_membership.job_title;
      return;
    end if;

    raise exception 'invitation has already been accepted';
  end if;

  if v_invitation.status = 'revoked' then
    raise exception 'invitation has been revoked';
  end if;

  if v_invitation.status = 'expired' or v_invitation.expires_at < v_now then
    raise exception 'invitation has expired';
  end if;

  select coalesce(active_user_limit, 5)
  into v_active_user_limit
  from public.organizations
  where id = v_invitation.organization_id
  for update;

  if coalesce(v_active_user_limit, 0) <= 0 then
    v_active_user_limit := 5;
  end if;

  update public.user_profiles
  set
    display_name = case
      when coalesce(trim(display_name), '') = '' and trim(coalesce(p_display_name, '')) <> '' then trim(p_display_name)
      else display_name
    end,
    updated_at = v_now
  where id = p_user_profile_id
    and lower(email) = lower(trim(p_email))
  returning coalesce(global_role, '') into v_user_global_role;

  if not found then
    raise exception 'user profile not found for invitation acceptance';
  end if;

  if lower(trim(coalesce(v_user_global_role, ''))) <> 'platform_admin' then
    select exists(
      select 1
      from public.organization_memberships m
      join public.user_profiles p on p.id = m.user_profile_id
      where m.organization_id = v_invitation.organization_id
        and m.user_profile_id = p_user_profile_id
        and m.membership_status = 'active'
        and p.account_status = 'active'
        and coalesce(p.global_role, '') <> 'platform_admin'
    )
    into v_existing_membership_active;

    select count(*)
    into v_active_user_count
    from public.organization_memberships m
    join public.user_profiles p on p.id = m.user_profile_id
    where m.organization_id = v_invitation.organization_id
      and m.membership_status = 'active'
      and p.account_status = 'active'
      and coalesce(p.global_role, '') <> 'platform_admin';

    if v_active_user_count >= v_active_user_limit and not v_existing_membership_active then
      raise exception 'active user limit reached for this organization';
    end if;
  end if;

  insert into public.organization_memberships (
    organization_id,
    user_profile_id,
    role,
    membership_status,
    team_name,
    job_title
  )
  values (
    v_invitation.organization_id,
    p_user_profile_id,
    v_invitation.role,
    'active',
    v_invitation.team_name,
    v_invitation.job_title
  )
  on conflict on constraint organization_memberships_org_user_unique do update
  set
    role = excluded.role,
    membership_status = 'active',
    team_name = case
      when coalesce(public.organization_memberships.team_name, '') = '' then excluded.team_name
      else public.organization_memberships.team_name
    end,
    job_title = case
      when coalesce(public.organization_memberships.job_title, '') = '' then excluded.job_title
      else public.organization_memberships.job_title
    end,
    updated_at = v_now
  returning * into v_membership;

  update public.invitations
  set
    status = 'accepted',
    accepted_at = coalesce(accepted_at, v_now),
    accepted_user_id = p_user_profile_id,
    updated_at = v_now
  where id = v_invitation.id;

  select o.name
  into v_org_name
  from public.organizations o
  where o.id = v_invitation.organization_id;

  return query
  select
    v_invitation.id,
    v_invitation.organization_id,
    coalesce(v_org_name, ''),
    v_membership.id,
    p_user_profile_id,
    v_membership.role,
    v_membership.membership_status,
    v_membership.team_name,
    v_membership.job_title;
end;
$$;

create or replace function public.apply_tracker_entry_override(
