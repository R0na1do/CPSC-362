-- Run only in a disposable local database after both files in supabase/.
-- Fake users and room rows are rolled back at the end.
begin;

insert into auth.users (id) values
    ('00000000-0000-0000-0000-000000000001'),
    ('00000000-0000-0000-0000-000000000002'),
    ('00000000-0000-0000-0000-000000000003');

create function pg_temp.check_result(ok boolean, label text) returns void
language plpgsql as $$
begin
    if ok is distinct from true then
        raise exception 'FAILED: %', label;
    end if;
end;
$$;

create function pg_temp.expect_error(statement text, expected text) returns void
language plpgsql as $$
begin
    begin
        execute statement;
    exception when others then
        if sqlerrm like '%' || expected || '%' then
            return;
        end if;
        raise;
    end;
    raise exception 'Expected error: %', expected;
end;
$$;

set local role authenticated;
select set_config('request.jwt.claim.sub', '', true);
select pg_temp.expect_error('select public.gg_create_room(''Host'')', 'SIGN_IN_REQUIRED');

select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-000000000001', true);
select set_config('test.room', public.gg_create_room('Host')->>'room_code', true);
select pg_temp.check_result(
    public.gg_create_room('Host')->>'room_code' = current_setting('test.room'),
    'repeated create returns the same waiting room'
);
select pg_temp.check_result(
    public.gg_get_room(current_setting('test.room'))->>'x_player_id'
        = '00000000-0000-0000-0000-000000000001',
    'host receives X'
);
select public.gg_join_room(current_setting('test.room'), 'Guest');
select pg_temp.check_result(
    public.gg_get_room(current_setting('test.room'))->>'o_player_id' is null,
    'host cannot fill both seats'
);
select pg_temp.expect_error(
    'update public."Games" set o_player_id = auth.uid()', 'permission denied'
);
select pg_temp.expect_error(
    'insert into public."Games" (room_code) values (''FAKECODE'')', 'permission denied'
);

select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-000000000002', true);
select pg_temp.check_result((select count(*) = 0 from public."Games"), 'outsider RLS read');
select pg_temp.expect_error(
    'select public.gg_get_room(current_setting(''test.room''))', 'ROOM_NOT_FOUND'
);
select pg_temp.expect_error('select public.gg_join_room(''BAD'', ''Guest'')', 'INVALID_ROOM_CODE');
select pg_temp.expect_error('select public.gg_join_room(''FFFFFFFF'', ''Guest'')', 'ROOM_NOT_FOUND');
select pg_temp.check_result(
    public.gg_join_room(lower(current_setting('test.room')), 'Guest')->>'o_player_id'
        = '00000000-0000-0000-0000-000000000002',
    'join assigns O to the authenticated caller'
);
select pg_temp.check_result(
    public.gg_join_room(current_setting('test.room'), 'Guest')->>'o_player_id'
        = '00000000-0000-0000-0000-000000000002',
    'repeat join keeps the same seat'
);
select pg_temp.check_result((select count(*) = 1 from public."Games"), 'guest can read room');

select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-000000000003', true);
select pg_temp.expect_error(
    'select public.gg_join_room(current_setting(''test.room''), ''Guest'')', 'ROOM_FULL'
);
select pg_temp.check_result((select count(*) = 0 from public."Games"), 'third player cannot read');

reset role;
update public."Games" set status = 'active' where room_code = current_setting('test.room');
set local role authenticated;
select pg_temp.expect_error(
    'select public.gg_join_room(current_setting(''test.room''), ''Guest'')', 'ROOM_NOT_WAITING'
);

reset role;
set local role anon;
select pg_temp.expect_error('select public.gg_create_room(''Host'')', 'permission denied');
select pg_temp.expect_error('select * from public."Games"', 'permission denied');
reset role;


-- Play real Classic rounds through the same functions the app will call.
set local role authenticated;
do $$
declare
    host text := '00000000-0000-0000-0000-000000000001';
    guest text := '00000000-0000-0000-0000-000000000002';
    outsider text := '00000000-0000-0000-0000-000000000003';
    code text;
    game jsonb;
    before_move jsonb;
    request uuid := gen_random_uuid();
    cell integer;
    line integer[];
    others integer[];
    moves integer[];
    expected text;
begin
    perform set_config('request.jwt.claim.sub', host, true);
    game := public.gg_create_room('Alice');
    code := game->>'room_code';
    perform pg_temp.expect_error(
        format('select public.gg_ready_room(%L)', code), 'WAIT_FOR_OPPONENT'
    );
    perform set_config('request.jwt.claim.sub', guest, true);
    game := public.gg_join_room(code, 'Bob');
    perform pg_temp.check_result(game->>'o_name' = 'Bob', 'guest display name');
    perform set_config('request.jwt.claim.sub', outsider, true);
    perform pg_temp.expect_error(
        format('select public.gg_ready_room(%L)', code), 'ROOM_NOT_FOUND'
    );
    perform pg_temp.expect_error(
        format('select public.gg_locked_room(%L)', code), 'permission denied'
    );

    perform set_config('request.jwt.claim.sub', host, true);
    game := public.gg_ready_room(code);
    perform pg_temp.check_result(game->>'status' = 'waiting', 'one ready does not start');
    perform pg_temp.expect_error(
        format('select public.gg_make_move(%L,0,%s,%L)', code, game->>'version', request),
        'GAME_NOT_ACTIVE'
    );
    perform set_config('request.jwt.claim.sub', guest, true);
    game := public.gg_ready_room(code);
    perform pg_temp.check_result(game->>'status' = 'active', 'both ready starts round');
    before_move := game;
    perform pg_temp.expect_error(
        format('select public.gg_make_move(%L,0,%s,%L)', code, game->>'version', request),
        'NOT_YOUR_TURN'
    );
    perform set_config('request.jwt.claim.sub', host, true);
    perform pg_temp.expect_error(
        format('select public.gg_make_move(%L,99,%s,%L)', code, game->>'version', request),
        'INVALID_CELL'
    );
    perform pg_temp.expect_error(
        format('select public.gg_make_move(%L,0,-1,%L)', code, request), 'STALE_ROOM'
    );
    perform pg_temp.check_result(
        public.gg_get_room(code) = before_move, 'rejections preserve every state field'
    );
    game := public.gg_make_move(code, 0, (game->>'version')::integer, request);
    perform pg_temp.check_result(
        public.gg_make_move(code, 0, (before_move->>'version')::integer, request) = game,
        'duplicate move does not place twice'
    );
    perform set_config('request.jwt.claim.sub', guest, true);
    perform pg_temp.expect_error(
        format('select public.gg_make_move(%L,0,%s,%L)', code, game->>'version', gen_random_uuid()),
        'CELL_OCCUPIED'
    );
    foreach cell in array array[3,1,4,2] loop
        perform set_config('request.jwt.claim.sub',
            case when game->>'turn' = 'x' then host else guest end, true);
        game := public.gg_make_move(code, cell, (game->>'version')::integer, gen_random_uuid());
    end loop;
    perform pg_temp.check_result(
        game->>'status' = 'finished' and game->>'winner' = 'x', 'winning round ends'
    );
    perform pg_temp.expect_error(
        format('select public.gg_make_move(%L,8,%s,%L)', code, game->>'version', gen_random_uuid()),
        'GAME_NOT_ACTIVE'
    );
    perform set_config('request.jwt.claim.sub', host, true);
    game := public.gg_rematch(code, 1);
    perform pg_temp.check_result(game->>'status' = 'finished', 'one rematch vote does not start');
    perform set_config('request.jwt.claim.sub', guest, true);
    game := public.gg_rematch(code, 1);
    perform pg_temp.check_result(
        game->>'status' = 'active' and game->>'turn' = 'o'
        and game->>'round_no' = '2' and game->>'move_count' = '0'
        and game->>'winner' is null, 'mutual rematch resets and alternates starter'
    );
    perform pg_temp.expect_error(
        format('select public.gg_rematch(%L,1)', code), 'STALE_ROOM'
    );
    perform pg_temp.expect_error(
        format('select public.gg_leave_room(%L,1)', code), 'STALE_ROOM'
    );
    game := public.gg_leave_room(code, 2);
    perform pg_temp.check_result(
        game->>'status' = 'finished' and game->>'winner' = 'x'
        and game->>'end_reason' = 'forfeit', 'leaving active round forfeits'
    );

    -- The existing Python tests use these same legal winning-line scenarios.
    foreach expected in array array['x','o'] loop
        foreach line slice 1 in array array[
            [0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]
        ] loop
            perform set_config('request.jwt.claim.sub', host, true);
            game := public.gg_create_room('Alice');
            code := game->>'room_code';
            perform set_config('request.jwt.claim.sub', guest, true);
            perform public.gg_join_room(code, 'Bob');
            perform public.gg_ready_room(code);
            perform set_config('request.jwt.claim.sub', host, true);
            game := public.gg_ready_room(code);
            others := array(select n from generate_series(0,8) n where not n = any(line));
            if expected = 'x' then
                moves := array[line[1],others[1],line[2],others[2],line[3]];
            else
                moves := array[others[1],line[1],others[2],line[2],others[6],line[3]];
            end if;
            foreach cell in array moves loop
                perform set_config('request.jwt.claim.sub',
                    case when game->>'turn' = 'x' then host else guest end, true);
                game := public.gg_make_move(code, cell, (game->>'version')::integer, gen_random_uuid());
            end loop;
            perform pg_temp.check_result(
                game->>'status' = 'finished' and game->>'winner' = expected,
                'all eight winning lines for both players'
            );
        end loop;
    end loop;

    foreach expected in array array['draw','win'] loop
        perform set_config('request.jwt.claim.sub', host, true);
        game := public.gg_create_room('Alice');
        code := game->>'room_code';
        perform set_config('request.jwt.claim.sub', guest, true);
        perform public.gg_join_room(code, 'Bob');
        perform public.gg_ready_room(code);
        perform set_config('request.jwt.claim.sub', host, true);
        game := public.gg_ready_room(code);
        moves := case when expected = 'draw' then array[0,1,2,4,3,5,7,6,8]
            else array[0,1,2,4,3,5,7,8,6] end;
        foreach cell in array moves loop
            perform set_config('request.jwt.claim.sub',
                case when game->>'turn' = 'x' then host else guest end, true);
            game := public.gg_make_move(code, cell, (game->>'version')::integer, gen_random_uuid());
        end loop;
        perform pg_temp.check_result(
            game->>'end_reason' = expected and game->>'status' = 'finished',
            'ninth-move win takes priority over draw'
        );
    end loop;
end;
$$;
reset role;


-- Five-digit generation, collision retries, and existing room compatibility.
reset role;
create temporary table code_retry_count (attempts integer);
insert into code_retry_count values (0);
create function pg_temp.force_one_collision() returns trigger language plpgsql as $$
begin
    if (select attempts from code_retry_count) = 0 then
        new.room_code := 'ABCDE123';
    end if;
    update code_retry_count set attempts = attempts + 1;
    return new;
end;
$$;
insert into public."Games" (room_code, x_player_id, board)
values ('ABCDE123', '00000000-0000-0000-0000-000000000001',
        '["", "", "", "", "", "", "", "", ""]'::jsonb);
create trigger force_code_collision before insert on public."Games"
    for each row execute function pg_temp.force_one_collision();
set local role authenticated;
select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-000000000003', true);
select set_config('test.new_room', public.gg_create_room('Code Test')->>'room_code', true);
select pg_temp.check_result(
    current_setting('test.new_room') ~ '^[0-9]{5}$', 'new codes contain exactly five digits'
);
reset role;
select pg_temp.check_result(
    (select attempts = 2 from code_retry_count), 'code collision retries without replacing room'
);
drop trigger force_code_collision on public."Games";
set local role authenticated;
select set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-000000000002', true);
select pg_temp.check_result(
    public.gg_join_room('abcde123', 'Legacy Guest')->>'room_code' = 'ABCDE123',
    'existing eight-character rooms still work'
);
reset role;

rollback;
