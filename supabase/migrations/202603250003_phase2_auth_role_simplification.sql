update public.users
set role = 'member'
where role not in ('admin', 'member');

update public.organization_memberships
set role = 'org_member'
where role not in ('org_admin', 'org_member');

update public.invitations
set role = 'org_member'
where role not in ('org_admin', 'org_member');

alter table public.users
  drop constraint if exists users_role_check;

alter table public.users
  add constraint users_role_check
  check (role in ('admin', 'member'));

alter table public.organization_memberships
  drop constraint if exists organization_memberships_role_check;

alter table public.organization_memberships
  add constraint organization_memberships_role_check
  check (role in ('org_admin', 'org_member'));

alter table public.invitations
  drop constraint if exists invitations_role_check;

alter table public.invitations
  add constraint invitations_role_check
  check (role in ('org_admin', 'org_member'));
