-- Apply locally after rooms.sql. Review both files before any live changes.
begin;

alter table public."Games"
    add column x_name text not null default 'Player X',
    add column o_name text,
    add column x_ready boolean not null default false,
    add column o_ready boolean not null default false,
    add column starter text not null default 'x' check (starter in ('x', 'o')),
    add column round_no integer not null default 1,
    add column version integer not null default 0,
    add column x_last_request uuid,
    add column o_last_request uuid,
    add column end_reason text;

create function public.gg_create_room(p_name text) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
    player uuid := auth.uid();
    game public."Games";
    code text;
begin
    if player is null then
        raise exception 'SIGN_IN_REQUIRED';
    end if;
    if p_name is null or length(btrim(p_name)) not between 1 and 20 then
        raise exception 'INVALID_NAME';
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
            room_code, board, x_moves, o_moves, x_player_id, x_name
        ) values (
            code, '["", "", "", "", "", "", "", "", ""]'::jsonb,
            '[]'::jsonb, '[]'::jsonb, player, btrim(p_name)
        ) on conflict (room_code) do nothing returning * into game;
        if found then
            return pg_catalog.to_jsonb(game);
        end if;
    end loop;
    raise exception 'ROOM_CODE_BUSY';
end;
$$;

create function public.gg_join_room(p_code text, p_name text) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
    player uuid := auth.uid();
    game public."Games";
    code text := pg_catalog.upper(pg_catalog.btrim(p_code));
begin
    if player is null then
        raise exception 'SIGN_IN_REQUIRED';
    end if;
    if p_name is null or length(btrim(p_name)) not between 1 and 20 then
        raise exception 'INVALID_NAME';
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

    update public."Games" set o_player_id = player, o_name = btrim(p_name), version = version + 1
        where id = game.id returning * into game;
    return pg_catalog.to_jsonb(game);
end;
$$;

-- Internal helper: the caller must be one of the two players.
create function public.gg_locked_room(p_code text) returns public."Games"
language plpgsql security invoker set search_path = '' as $$
declare
    game public."Games";
begin
    if auth.uid() is null then
        raise exception 'SIGN_IN_REQUIRED';
    end if;
    select * into game from public."Games"
        where room_code = upper(btrim(p_code)) for update;
    if not found or (
        auth.uid() is distinct from game.x_player_id
        and auth.uid() is distinct from game.o_player_id
    ) then
        raise exception 'ROOM_NOT_FOUND';
    end if;
    return game;
end;
$$;

create function public.gg_ready_room(p_code text) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
    game public."Games" := public.gg_locked_room(p_code);
begin
    if game.status <> 'waiting' then
        return to_jsonb(game);
    end if;
    if game.o_player_id is null then
        raise exception 'WAIT_FOR_OPPONENT';
    end if;
    if auth.uid() = game.x_player_id then
        game.x_ready := true;
    else
        game.o_ready := true;
    end if;
    update public."Games" set x_ready = game.x_ready, o_ready = game.o_ready,
        status = case when game.x_ready and game.o_ready then 'active' else 'waiting' end,
        version = version + 1
        where id = game.id returning * into game;
    return to_jsonb(game);
end;
$$;

create function public.gg_make_move(
    p_code text, p_cell integer, p_version integer, p_request uuid
) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
    game public."Games" := public.gg_locked_room(p_code);
    mark text;
    line integer[];
begin
    mark := case when auth.uid() = game.x_player_id then 'x' else 'o' end;
    if p_request is null then
        raise exception 'INVALID_REQUEST';
    end if;
    if (mark = 'x' and game.x_last_request = p_request)
        or (mark = 'o' and game.o_last_request = p_request) then
        return to_jsonb(game);
    end if;
    if game.status <> 'active' then
        raise exception 'GAME_NOT_ACTIVE';
    end if;
    if p_version is distinct from game.version then
        raise exception 'STALE_ROOM';
    end if;
    if game.turn <> mark then
        raise exception 'NOT_YOUR_TURN';
    end if;
    if p_cell is null or p_cell not between 0 and 8 then
        raise exception 'INVALID_CELL';
    end if;
    if game.board->>p_cell <> '' then
        raise exception 'CELL_OCCUPIED';
    end if;

    game.board := jsonb_set(game.board, array[p_cell::text], to_jsonb(mark));
    game.move_count := game.move_count + 1;
    foreach line slice 1 in array array[
        [0,1,2], [3,4,5], [6,7,8], [0,3,6],
        [1,4,7], [2,5,8], [0,4,8], [2,4,6]
    ] loop
        if game.board->>line[1] = mark and game.board->>line[2] = mark
            and game.board->>line[3] = mark then
            game.winner := mark;
            exit;
        end if;
    end loop;
    if game.winner is not null or game.move_count = 9 then
        game.status := 'finished';
        game.x_ready := false;
        game.o_ready := false;
        game.end_reason := case when game.winner is null then 'draw' else 'win' end;
    else
        game.turn := case when mark = 'x' then 'o' else 'x' end;
    end if;
    update public."Games" set board = game.board, move_count = game.move_count,
        turn = game.turn, winner = game.winner, status = game.status,
        end_reason = game.end_reason,
        x_ready = game.x_ready, o_ready = game.o_ready, version = version + 1,
        x_last_request = case when mark = 'x' then p_request else x_last_request end,
        o_last_request = case when mark = 'o' then p_request else o_last_request end
        where id = game.id returning * into game;
    return to_jsonb(game);
end;
$$;

create function public.gg_rematch(p_code text, p_round integer) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
    game public."Games" := public.gg_locked_room(p_code);
begin
    if p_round is distinct from game.round_no then
        raise exception 'STALE_ROOM';
    end if;
    if game.status <> 'finished' then
        return to_jsonb(game);
    end if;
    if auth.uid() = game.x_player_id then
        game.x_ready := true;
    else
        game.o_ready := true;
    end if;
    if game.x_ready and game.o_ready then
        game.starter := case when game.starter = 'x' then 'o' else 'x' end;
        game.turn := game.starter;
        game.board := '["", "", "", "", "", "", "", "", ""]'::jsonb;
        game.move_count := 0;
        game.winner := null;
        game.status := 'active';
        game.round_no := game.round_no + 1;
        game.end_reason := null;
    end if;
    update public."Games" set x_ready = game.x_ready, o_ready = game.o_ready,
        starter = game.starter, turn = game.turn, board = game.board,
        move_count = game.move_count, winner = game.winner, status = game.status,
        round_no = game.round_no, end_reason = game.end_reason, version = version + 1
        where id = game.id returning * into game;
    return to_jsonb(game);
end;
$$;

create function public.gg_leave_room(p_code text, p_round integer) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
    game public."Games" := public.gg_locked_room(p_code);
begin
    if p_round is distinct from game.round_no then
        raise exception 'STALE_ROOM';
    end if;
    if game.status = 'active' then
        game.status := 'finished';
        game.winner := case when auth.uid() = game.x_player_id then 'o' else 'x' end;
        game.x_ready := false;
        game.o_ready := false;
        game.end_reason := 'forfeit';
    elsif game.status = 'waiting' and auth.uid() = game.x_player_id then
        game.status := 'abandoned';
    elsif game.status = 'waiting' then
        game.o_player_id := null;
        game.o_name := null;
        game.x_ready := false;
        game.o_ready := false;
    end if;
    update public."Games" set status = game.status, winner = game.winner,
        o_player_id = game.o_player_id, o_name = game.o_name,
        x_ready = game.x_ready, o_ready = game.o_ready,
        end_reason = game.end_reason, version = version + 1
        where id = game.id returning * into game;
    return to_jsonb(game);
end;
$$;


-- Retire the earlier lobby-only entry points after installing the named versions.
revoke all on function public.gg_create_room() from public, anon, authenticated;
revoke all on function public.gg_join_room(text) from public, anon, authenticated;
revoke all on function public.gg_locked_room(text) from public, anon, authenticated;
revoke all on function public.gg_create_room(text) from public, anon, authenticated;
revoke all on function public.gg_join_room(text, text) from public, anon, authenticated;
revoke all on function public.gg_ready_room(text) from public, anon, authenticated;
revoke all on function public.gg_make_move(text, integer, integer, uuid) from public, anon, authenticated;
revoke all on function public.gg_rematch(text, integer) from public, anon, authenticated;
revoke all on function public.gg_leave_room(text, integer) from public, anon, authenticated;
grant execute on function public.gg_create_room(text) to authenticated;
grant execute on function public.gg_join_room(text, text) to authenticated;
grant execute on function public.gg_ready_room(text) to authenticated;
grant execute on function public.gg_make_move(text, integer, integer, uuid) to authenticated;
grant execute on function public.gg_rematch(text, integer) to authenticated;
grant execute on function public.gg_leave_room(text, integer) to authenticated;
notify pgrst, 'reload schema';
commit;
