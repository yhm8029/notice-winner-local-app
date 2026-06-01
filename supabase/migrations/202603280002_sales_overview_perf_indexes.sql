create index if not exists idx_project_sales_claims_org_active_claimed_at
  on public.project_sales_claims (organization_id, claimed_at desc)
  where is_active = true;

create index if not exists idx_organization_memberships_org_status_user
  on public.organization_memberships (organization_id, membership_status, user_profile_id);
