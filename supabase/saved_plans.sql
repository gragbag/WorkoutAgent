create extension if not exists pgcrypto;

create table if not exists public.saved_plans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  summary text not null,
  metadata jsonb not null default '{}'::jsonb,
  days jsonb not null default '[]'::jsonb,
  optional_days jsonb not null default '[]'::jsonb,
  coaching_notes jsonb not null default '[]'::jsonb,
  athlete_snapshot jsonb not null default '[]'::jsonb,
  intake jsonb not null default '{}'::jsonb,
  saved_at timestamptz not null default timezone('utc', now())
);

alter table public.saved_plans enable row level security;

create policy "users can view their own saved plans"
on public.saved_plans
for select
using (auth.uid() = user_id);

create policy "users can insert their own saved plans"
on public.saved_plans
for insert
with check (auth.uid() = user_id);

create policy "users can delete their own saved plans"
on public.saved_plans
for delete
using (auth.uid() = user_id);
