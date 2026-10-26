-- Apply after online_classic.sql. Existing room codes and permissions stay intact.
begin;

create or replace function public.gg_create_room(p_name text) returns jsonb
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

    for attempt in 1..20 loop
        code := pg_catalog.lpad(
            ((('x' || pg_catalog.substr(pg_catalog.gen_random_uuid()::text, 1, 8))
                ::bit(32)::bigint) % 100000)::text, 5, '0'
        );
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

create or replace function public.gg_join_room(p_code text, p_name text) returns jsonb
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
    if code is null or code !~ '^([0-9]{5}|[0-9A-F]{8})$' then
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


notify pgrst, 'reload schema';
commit;
