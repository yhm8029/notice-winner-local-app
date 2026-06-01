alter table public.pipeline_runs
  drop constraint if exists pipeline_runs_run_type_check;

update public.pipeline_runs
set run_type = 'project_tracker'
where run_type = 'winner_pipeline';

alter table public.pipeline_runs
  add constraint pipeline_runs_run_type_check
  check (run_type in ('project_tracker', 'tracker_export'));
