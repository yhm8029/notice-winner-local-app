create table if not exists public.login_audit_logs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid not null,
  user_email text not null,
  user_role text not null,
  ip_address text not null,
  user_agent text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_login_audit_logs_org_created
  on public.login_audit_logs (organization_id, created_at desc);
