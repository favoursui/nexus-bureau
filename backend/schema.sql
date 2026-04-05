-- Tasks
create table tasks (
    id uuid primary key default gen_random_uuid(),
    user_input text not null,
    status text not null default 'pending',
    created_at timestamp with time zone default now()
);

-- Transactions
create table transactions (
    id uuid primary key default gen_random_uuid(),
    task_id uuid references tasks(id) on delete cascade,
    api_url text not null,
    amount numeric not null,
    currency text not null default 'USDC',
    stellar_hash text not null,
    created_at timestamp with time zone default now()
);

-- Results
create table results (
    id uuid primary key default gen_random_uuid(),
    task_id uuid references tasks(id) on delete cascade,
    summary text not null,
    sources text[] not null default '{}',
    created_at timestamp with time zone default now()
);