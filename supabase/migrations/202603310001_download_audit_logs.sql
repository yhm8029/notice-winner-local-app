create table if not exists public.download_audit_logs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid null,
  user_email text not null,
  user_role text not null,
  download_scope text not null,
  download_format text not null,
  source_page text not null,
  file_name text not null,
  created_at timestamptz not null default now(),
  constraint download_audit_logs_download_scope_check
    check (download_scope in ('my', 'company', 'global')),
  constraint download_audit_logs_download_format_check
    check (download_format in ('xlsx', 'csv')),
  constraint download_audit_logs_source_page_check
    check (source_page in ('my_active_sales', 'company_active_sales', 'tracker_entries'))
);

create index if not exists idx_download_audit_logs_org_created
  on public.download_audit_logs (organization_id, created_at desc);

create index if not exists idx_download_audit_logs_org_source_created
  on public.download_audit_logs (organization_id, source_page, created_at desc);
