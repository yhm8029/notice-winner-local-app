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
  released_at timestamptz,
  is_active boolean not null default true,
  sales_note text not null default '',
  sales_note_updated_at timestamptz,
  sales_note_updated_by uuid references public.users(id) on delete set null,
  estimated_amount_text text not null default '',
  estimated_amount_low_krw bigint,
  estimated_amount_high_krw bigint,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
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
    check (event_type in ('claim', 'release', 'force_release', 'note_update'))
);

create index if not exists idx_project_sales_claim_events_claim
  on public.project_sales_claim_events (claim_id, id desc);
