-- Review before applying to Supabase. This first lobby supports Classic, untimed.
begin;

-- Stop instead of replacing unknown teammate policies or functions.
do $$
begin
    if exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'Games'
    ) or exists (
        select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
        where n.nspname = 'public' and p.prosrc like '%Games%'
    ) then
        raise exception 'Review existing Games policies and functions before applying rooms.sql';
    end if;
end;
$$;

alter table public."Games"
    add column x_player_id uuid references auth.users(id),
    add column o_player_id uuid references auth.users(id),
    add constraint games_different_players check (x_player_id <> o_player_id);

alter table public."Games" enable row level security;
revoke all on public."Games" from public, anon, authenticated;
grant select on public."Games" to authenticated;

create policy games_participant_read on public."Games"
    for select to authenticated
    using (auth.uid() = x_player_id or auth.uid() = o_player_id);

-- Seat writes go through these functions, not direct browser updates.
create function public.gg_create_room() returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
    player uuid := auth.uid();
    game public."Games";
    code text;
begin
    if player is null then
        raise exception 'SIGN_IN_REQUIRED';
    end if;

    perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(player::text, 0));
    select * into game from public."Games"
        where x_player_id = player and status = 'waiting'
        order by created_at desc limit 1;
    if found then
        return pg_catalog.to_jsonb(game);
    end if;

    for attempt in 1..5 loop
        code := pg_catalog.upper(pg_catalog.substr(
            pg_catalog.replace(pg_catalog.gen_random_uuid()::text, '-', ''), 1, 8
        ));
        insert into public."Games" (
            room_code, board, x_moves, o_moves, x_player_id
        ) values (
            code, '["", "", "", "", "", "", "", "", ""]'::jsonb,
            '[]'::jsonb, '[]'::jsonb, player
        ) on conflict (room_code) do nothing returning * into game;
        if found then
            return pg_catalog.to_jsonb(game);
        end if;
    end loop;
    raise exception 'ROOM_CODE_BUSY';
end;
$$;

create function public.gg_join_room(p_code text) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
    player uuid := auth.uid();
    game public."Games";
    code text := pg_catalog.upper(pg_catalog.btrim(p_code));
begin
    if player is null then
        raise exception 'SIGN_IN_REQUIRED';
    end if;
    if code is null or code !~ '^[0-9A-F]{8}$' then
        raise exception 'INVALID_ROOM_CODE';
    end if;

    select * into game from public."Games" where room_code = code for update;
    if not found or game.x_player_id is null then
        raise exception 'ROOM_NOT_FOUND';
    end if;
    if game.x_player_id = player or game.o_player_id = player then
        return pg_catalog.to_jsonb(game);
    end if;
    if game.status <> 'waiting' then
        raise exception 'ROOM_NOT_WAITING';
    end if;
    if game.o_player_id is not null then
        raise exception 'ROOM_FULL';
    end if;

    update public."Games" set o_player_id = player
        where id = game.id returning * into game;
    return pg_catalog.to_jsonb(game);
end;
$$;

create function public.gg_get_room(p_code text) returns jsonb
language plpgsql security invoker set search_path = '' as $$
declare
    game public."Games";
begin
    if auth.uid() is null then
        raise exception 'SIGN_IN_REQUIRED';
    end if;
    select * into game from public."Games"
        where room_code = pg_catalog.upper(pg_catalog.btrim(p_code));
    if not found then
        raise exception 'ROOM_NOT_FOUND';
    end if;
    return pg_catalog.to_jsonb(game);
end;
$$;

revoke all on function public.gg_create_room() from public, anon, authenticated;
revoke all on function public.gg_join_room(text) from public, anon, authenticated;
revoke all on function public.gg_get_room(text) from public, anon, authenticated;
grant execute on function public.gg_create_room() to authenticated;
grant execute on function public.gg_join_room(text) to authenticated;
grant execute on function public.gg_get_room(text) to authenticated;

commit;
