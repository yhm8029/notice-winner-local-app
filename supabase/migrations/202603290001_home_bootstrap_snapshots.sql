create table if not exists public.home_bootstrap_snapshots (
  organization_id uuid primary key,
  snapshot_version integer not null default 1,
  payload_json jsonb not null default '{}'::jsonb,
  generated_at timestamptz null,
  invalidated_at timestamptz null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists home_bootstrap_snapshots_generated_at_idx
  on public.home_bootstrap_snapshots (generated_at desc);

create or replace function public.touch_home_bootstrap_snapshots_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists trg_touch_home_bootstrap_snapshots_updated_at on public.home_bootstrap_snapshots;
create trigger trg_touch_home_bootstrap_snapshots_updated_at
before update on public.home_bootstrap_snapshots
for each row
execute function public.touch_home_bootstrap_snapshots_updated_at();
