alter table public.users
  add column if not exists status text not null default 'active';

alter table public.users
  drop constraint if exists users_status_check;

alter table public.users
  add constraint users_status_check
    check (status in ('active', 'inactive', 'deactivated'));

alter table public.project_sales_claims
  add column if not exists current_owner_assigned_at timestamptz;

update public.project_sales_claims
set current_owner_assigned_at = claimed_at
where current_owner_assigned_at is null;

alter table public.project_sales_claims
  alter column current_owner_assigned_at set default now();

alter table public.project_sales_claims
  alter column current_owner_assigned_at set not null;

alter table public.project_sales_claims
  add column if not exists claim_status text not null default 'active';

update public.project_sales_claims
set claim_status = 'active'
where claim_status is null;

alter table public.project_sales_claims
  drop constraint if exists project_sales_claims_status_check;

alter table public.project_sales_claims
  add constraint project_sales_claims_status_check
    check (claim_status in ('active', 'won', 'lost'));

alter table public.project_sales_claims
  add column if not exists closed_at timestamptz;

alter table public.project_sales_claims
  add column if not exists closed_by uuid references public.users(id) on delete set null;

create index if not exists idx_project_sales_claims_owner_active
  on public.project_sales_claims (organization_id, owner_user_id, current_owner_assigned_at desc)
  where is_active = true and claim_status = 'active';

alter table public.project_sales_claim_events
  drop constraint if exists project_sales_claim_events_type_check;

alter table public.project_sales_claim_events
  add constraint project_sales_claim_events_type_check
    check (event_type in ('claim', 'release', 'force_release', 'note_update', 'transfer', 'close_won', 'close_lost'));
