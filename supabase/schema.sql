-- Run this in Supabase Dashboard > SQL Editor.
-- Each signed-in user can access only their own enrichment history.
create table if not exists public.enrichment_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  brand text not null,
  mpn text not null,
  description text not null,
  result jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists enrichment_runs_user_created_at_idx
  on public.enrichment_runs (user_id, created_at desc);

alter table public.enrichment_runs enable row level security;

create policy "Users read their own enrichment history"
  on public.enrichment_runs for select
  to authenticated using ((select auth.uid()) = user_id);

create policy "Users insert their own enrichment history"
  on public.enrichment_runs for insert
  to authenticated with check ((select auth.uid()) = user_id);
