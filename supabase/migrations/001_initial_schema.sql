create extension if not exists pgcrypto;

create table projects (
    id uuid primary key default gen_random_uuid(),
    slug text not null unique,
    name text not null,
    created_at timestamptz not null default now()
);

create table runs (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references projects(id) on delete cascade,
    status text not null check (status in ('completed', 'failed')),
    summary text not null,
    created_at timestamptz not null default now()
);

create table documents (
    id uuid primary key default gen_random_uuid(),
    run_id uuid not null references runs(id) on delete cascade,
    source_document_id text not null,
    file_name text not null,
    content text not null,
    unique (run_id, source_document_id)
);

create table document_chunks (
    id uuid primary key default gen_random_uuid(),
    run_id uuid not null references runs(id) on delete cascade,
    document_id uuid not null references documents(id) on delete cascade,
    source_chunk_id text not null,
    chunk_index integer not null check (chunk_index >= 0),
    text text not null,
    source_label text not null,
    unique (run_id, source_chunk_id)
);

create table facts (
    id uuid primary key default gen_random_uuid(),
    run_id uuid not null references runs(id) on delete cascade,
    document_chunk_id uuid not null references document_chunks(id) on delete cascade,
    source_fact_id text not null,
    category text not null,
    claim text not null,
    evidence_quote text not null,
    source_document text not null,
    confidence double precision not null check (confidence between 0 and 1),
    unique (run_id, source_fact_id)
);

create table questions (
    id uuid primary key default gen_random_uuid(),
    run_id uuid not null references runs(id) on delete cascade,
    source_question_id text not null,
    position integer not null check (position >= 0),
    question_text text not null,
    required_control text not null,
    risk_domain text not null,
    unique (run_id, source_question_id)
);

create table answers (
    id uuid primary key default gen_random_uuid(),
    run_id uuid not null references runs(id) on delete cascade,
    question_id uuid not null references questions(id) on delete cascade,
    position integer not null check (position >= 0),
    status text not null check (status in ('SUPPORTED', 'PARTIAL', 'DEFICIT')),
    answer_text text not null,
    policy_reason text not null,
    citations jsonb not null default '[]'::jsonb,
    cited_fact_ids jsonb not null default '[]'::jsonb,
    unique (run_id, question_id)
);

create table remediation_tasks (
    id uuid primary key default gen_random_uuid(),
    run_id uuid not null references runs(id) on delete cascade,
    question_id uuid not null references questions(id) on delete cascade,
    title text not null,
    description text not null,
    severity text not null,
    suggested_owner text not null,
    unique (run_id, question_id)
);

create index documents_run_id_idx on documents(run_id);
create index document_chunks_run_id_idx on document_chunks(run_id);
create index facts_run_id_idx on facts(run_id);
create index questions_run_id_idx on questions(run_id);
create index answers_run_id_idx on answers(run_id);
create index remediation_tasks_run_id_idx on remediation_tasks(run_id);

comment on table runs is
    'Immutable snapshots of governed verification runs. RLS is intentionally deferred until authentication work.';
