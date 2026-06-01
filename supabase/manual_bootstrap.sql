-- Manual bootstrap entry point.
-- Run this with psql or a compatible runner so the include directives resolve.

\ir manual_bootstrap_parts/00_core_schema.sql
\ir manual_bootstrap_parts/01_tracker_schema.sql
\ir manual_bootstrap_parts/02_invitation_functions.sql
\ir manual_bootstrap_parts/03_tracker_overrides_and_sales.sql
