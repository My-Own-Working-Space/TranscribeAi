-- TranscribeAI Supabase Schema
-- Run this in Supabase Dashboard > SQL Editor

-- 1. Profiles (linked to auth.users)
create table if not exists public.profiles (
  id uuid references auth.users(id) on delete cascade primary key,
  email text not null,
  full_name text default '',
  plan text default 'free',
  monthly_minutes_used integer default 0,
  monthly_minutes_limit integer default 9999,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- 2. Transcription Jobs
create table if not exists public.transcription_jobs (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  status text default 'queued',
  original_filename text,
  storage_path text,
  file_size_bytes integer default 0,
  duration_seconds float default 0.0,
  whisper_model text default 'base',
  language_detected text,
  overall_confidence float default 0.0,
  processing_time_s float default 0.0,
  transcript text default '',
  segments_json jsonb default '[]'::jsonb,  -- [{index, start, end, text, confidence, speaker}]
  mode text default 'standard',
  error text,
  created_at timestamptz default now(),
  completed_at timestamptz
);

create index if not exists idx_jobs_user on public.transcription_jobs(user_id);
create index if not exists idx_jobs_created on public.transcription_jobs(created_at desc);

-- 3. Transcript Segments (DEPRECATED — kept for migration, new data in transcription_jobs.segments_json)
create table if not exists public.transcript_segments (
  id uuid default gen_random_uuid() primary key,
  job_id uuid references public.transcription_jobs(id) on delete cascade not null,
  segment_index integer not null,
  start_time float not null,
  end_time float not null,
  content text not null,
  confidence float default 0.0,
  speaker_label text
);

create index if not exists idx_segments_job on public.transcript_segments(job_id);

-- 4. AI Summaries
create table if not exists public.ai_summaries (
  id uuid default gen_random_uuid() primary key,
  job_id uuid references public.transcription_jobs(id) on delete cascade unique not null,
  summary text,
  key_points jsonb,
  conclusion text,
  llm_model text,
  review_passes integer default 0,
  generated_at timestamptz default now()
);

-- 5. Action Items
create table if not exists public.action_items (
  id uuid default gen_random_uuid() primary key,
  job_id uuid references public.transcription_jobs(id) on delete cascade not null,
  task_description text not null,
  assignee text default 'Unassigned',
  deadline text default 'Not specified',
  priority text default 'medium',
  is_completed boolean default false,
  created_at timestamptz default now()
);

create index if not exists idx_actions_job on public.action_items(job_id);

-- 6. Chat Messages (DEPRECATED — chat sessions now stored in Redis)
create table if not exists public.chat_messages (
  id uuid default gen_random_uuid() primary key,
  job_id uuid references public.transcription_jobs(id) on delete cascade not null,
  user_id uuid references public.profiles(id) on delete cascade not null,
  role text not null,
  content text not null,
  created_at timestamptz default now()
);

create index if not exists idx_chat_job on public.chat_messages(job_id);

-- 7. Feedback
create table if not exists public.feedback (
  id uuid default gen_random_uuid() primary key,
  user_id uuid,  -- optional, no FK — works for anonymous users
  name text default '',
  email text default '',
  feedback_type text default 'general',
  message text not null,
  created_at timestamptz default now()
);

-- Feedback: anyone can insert, only service role can read
alter table public.feedback enable row level security;
create policy "Anyone can insert feedback" on public.feedback for insert with check (true);

-- ═══════════════════════════════════════════════
-- Row Level Security (RLS)
-- ═══════════════════════════════════════════════

alter table public.profiles enable row level security;
alter table public.transcription_jobs enable row level security;
alter table public.transcript_segments enable row level security;  -- DEPRECATED
alter table public.ai_summaries enable row level security;
alter table public.action_items enable row level security;
alter table public.chat_messages enable row level security;  -- DEPRECATED

-- Profiles: users can read/update their own profile
create policy "Users read own profile" on public.profiles for select using (auth.uid() = id);
create policy "Users update own profile" on public.profiles for update using (auth.uid() = id);

-- Jobs: users can CRUD their own jobs
create policy "Users read own jobs" on public.transcription_jobs for select using (auth.uid() = user_id);
create policy "Users insert own jobs" on public.transcription_jobs for insert with check (auth.uid() = user_id);
create policy "Users delete own jobs" on public.transcription_jobs for delete using (auth.uid() = user_id);
create policy "Users update own jobs" on public.transcription_jobs for update using (auth.uid() = user_id);

-- Segments: via job ownership
create policy "Users read own segments" on public.transcript_segments for select
  using (job_id in (select id from public.transcription_jobs where user_id = auth.uid()));
create policy "Users insert own segments" on public.transcript_segments for insert
  with check (job_id in (select id from public.transcription_jobs where user_id = auth.uid()));

-- Summaries: via job ownership
create policy "Users read own summaries" on public.ai_summaries for select
  using (job_id in (select id from public.transcription_jobs where user_id = auth.uid()));
create policy "Users insert own summaries" on public.ai_summaries for insert
  with check (job_id in (select id from public.transcription_jobs where user_id = auth.uid()));
create policy "Users update own summaries" on public.ai_summaries for update
  using (job_id in (select id from public.transcription_jobs where user_id = auth.uid()));

-- Actions: via job ownership
create policy "Users read own actions" on public.action_items for select
  using (job_id in (select id from public.transcription_jobs where user_id = auth.uid()));
create policy "Users insert own actions" on public.action_items for insert
  with check (job_id in (select id from public.transcription_jobs where user_id = auth.uid()));
create policy "Users update own actions" on public.action_items for update
  using (job_id in (select id from public.transcription_jobs where user_id = auth.uid()));

-- Chat: via job ownership
create policy "Users read own chat" on public.chat_messages for select
  using (job_id in (select id from public.transcription_jobs where user_id = auth.uid()));
create policy "Users insert own chat" on public.chat_messages for insert
  with check (job_id in (select id from public.transcription_jobs where user_id = auth.uid()));

-- ═══════════════════════════════════════════════
-- Auto-create profile on signup
-- ═══════════════════════════════════════════════

create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name)
  values (new.id, new.email, coalesce(new.raw_user_meta_data->>'full_name', ''));
  return new;
end;
$$ language plpgsql security definer;

create or replace trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
