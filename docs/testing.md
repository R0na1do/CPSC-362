# Graffiti Grid setup and checks

## Run the app

Windows PowerShell, from the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

On macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

Skip environment creation if `.venv` exists. Open http://127.0.0.1:8080.
Stop with Ctrl+C. Restart after code or `.env` changes.
Windows skips the unsupported `uvloop` package.

## Supabase

Keep the project URL and publishable key in `.env`, using `.env.example` as a
reference. `.env` stays out of Git. Never use a secret or service-role key.
Anonymous sign-ins must be enabled. If CAPTCHA is required, keep it enabled;
this version does not support it yet.

Database files, in order:

1. `supabase/rooms.sql`: two player seats and participant-only access.
2. `supabase/online_classic.sql`: readiness, moves, results, rematches, and leaving.
3. `supabase/five_digit_codes.sql`: five-digit codes, with old-code compatibility.

The first two were applied through MCP after the broad "Allow game access"
policy was reviewed and replaced. Do not rerun them. The five-digit update is
tested locally but has not been confirmed applied to Supabase.
Keep the safety guards and RLS enabled. Review database changes before applying.
No existing game rows are deleted by these scripts.

## Play and check

- Classic: take turns, play a win and a draw, then try Play Again.
- Blitz: a fourth piece removes that player's oldest piece; test the turn timer.
- Online: open two tabs and sign in separately. Enter player names.
- Click CREATE ROOM to generate a code. Paste that actual code into
  Code from the host in the other tab, then click JOIN ROOM.
- Both players click READY. Play a round, then both request REMATCH.
  The starter alternates. A third player cannot join a full room.
- LEAVE ROOM asks for confirmation and forfeits an active round.
  BACK TO MENU keeps the room open.

Refreshing the page loses the guest session. Keep test tabs open.
New five-digit codes keep leading zeros. Existing eight-character rooms still
work; leave an old waiting room before creating one with a new code.
Two computers can each run the app using the same Supabase project settings.
Public hosting is not configured.

## Tests and limits

```bash
python -B -m unittest discover -v
```

Use `python3` on macOS. Expected result: **42 tests, OK**.
These tests use fake provider responses and need no database connection.
For SQL tests, apply all three database files to a disposable local database,
then run `tests/rooms.sql`. Its test rows roll back. Do not run it in production.

Passed checks include local rules, live room creation/joining, readiness,
validated moves, wins/draws, mutual rematches, duplicate rejection, permissions,
and simultaneous joins. Browser checks covered desktop/phone layouts, X/O
alignment, Create/Join controls, and the local Blitz timer. Live tests added test
guests and two isolated rooms; existing data was preserved.

Actual macOS and iPhone Safari remain untested. Matchmaking, online Blitz/timers,
history, refresh/reconnect recovery, CAPTCHA, and join rate limits are unfinished.
This is the agreed basic version, not every planned feature in `requirements.md`
and not a release for unrestricted public hosting.

## Lecture techniques

These references were checked in the slide text from the supplied course ZIP:

- **Modular design:** `Ch 6 - Quality and Security.key`, 6.1.2.
  Screens, local rules, sign-in, and room requests have separate jobs.
- **Testing:** the same file, 6.2.4. Test rules and permissions before claiming success.
- **Cohesion/coupling:** `Ch 11 - Component level design.key`, 11.2.3-11.2.4.
  Room requests stay together in `rooms.py`; SQL stays out of the screens.
- **Traceability:** `Ch 7 Requirements Engineering.key`, 7.2.6.
  Room tests check the private-room and security requirements in sections 4 and 6.

For the exact Supabase API, SQL locking/permissions, and Windows package condition:
This is not covered in the provided notes. Those details use official documentation.
A matching responsive CSS example was not verified in the notes. The implementation
is not claimed to be 100 percent lecture-derived.
