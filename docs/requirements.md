# Tic-Tac-Toe Blitz — Project Requirements

## 1. Project Goal

Build a browser-based tic-tac-toe game where two players can
compete through private rooms or matchmaking.

Development will use Next.js, TypeScript, Supabase, GitHub,
and VS Code. Hosting will be selected after local testing.

This document describes planned features, not completed work.

## 2. Game Modes

### Classic

- Use a 3 × 3 board.
- Players alternate X and O.
- Players may select only empty squares.
- Three matching pieces horizontally, vertically, or diagonally win.
- A full board without a winner is a draw.
- The default timer is off.

### Blitz

- Use the same board and winning conditions as Classic.
- Each player may have at most three active pieces.
- On a fourth valid placement, remove that player's oldest piece.
- Check for a win after removing the oldest piece.
- Highlight the oldest piece so players can anticipate removal.
- The default timer is 30 seconds per turn.

## 3. Shared Rules

- Invalid moves must not change the board, turn, or deadline.
- Occupied squares cannot be selected, including an oldest piece.
- Timer options for private rooms: Off, 15, 30, or 60 seconds.
- Timer expiration skips the turn without removing pieces.
- A move received by the server at or after the deadline is rejected.
- A third occurrence of the same full state produces a draw.
- Full state includes the board, next player, and piece queue order.
- A round ends in a draw after 100 actions.
- An action is a valid placement or a timed-out turn.
- A winning move takes priority over draw limits.
- Finished rounds reject additional moves.

## 4. Private Rooms

- A player selects a mode and timer and creates a room.
- The system generates a random room code.
- Another player enters the code to join.
- Each room has exactly two player seats.
- Additional players cannot join a full room.
- Both players must confirm readiness before the match starts.
- Settings lock when the match starts.
- Rematches require both players to agree and alternate the starter.

## 5. Quick Match

- Players choose Classic or Blitz before entering the queue.
- Classic matchmaking uses an untimed match.
- Blitz matchmaking uses a 30-second turn timer.
- Pair only players with compatible settings.
- Players may cancel while waiting.
- A player cannot have multiple active queue entries or matches.
- Matchmaking must claim players atomically to prevent duplicates.

## 6. Multiplayer Security

- Each player must have a Supabase-authenticated identity.
- Guest sign-in may be used without requiring an email account.
- The server determines player identity, X/O assignment, and turns.
- The server validates moves and calculates results.
- Browser-submitted boards, winners, or timestamps are not trusted.
- Joining seats and applying moves must be atomic.
- Database permissions restrict match data to authorized participants.
- Room codes locate rooms; they do not replace authorization.
- Privileged keys must stay out of browser code and GitHub.
- Duplicate requests must not produce duplicate moves or results.
- Add rate limits to authentication, room joining, and matchmaking.

## 7. Disconnects and Recovery

- Allow a disconnected player 30 seconds to reconnect.
- The match clock continues during the reconnect period.
- A valid game outcome reached first remains final.
- Otherwise, record a forfeit after the reconnect period if the
  opponent remains connected.
- If both players remain disconnected, abandon the match without
  awarding a win.
- The server must determine connection status and recovery deadlines.

## 8. Interface and History

- Show player names, mode, current turn, and match status.
- Show remaining time when the timer is enabled.
- Immediately display server-confirmed board updates.
- Animate Blitz removal and highlight winning cells.
- Keep controls usable on desktop and mobile screens.
- Save completed matches once.
- Display match history only to authorized participants.

## 9. Acceptance Checks

- A third player is rejected from a full room.
- Simultaneous joins cannot claim the same seat.
- Out-of-turn and occupied-square moves are rejected.
- A fourth Blitz placement removes the correct oldest piece.
- Both players see the same server-confirmed state.
- Timeouts switch turns exactly once.
- Duplicate move requests cannot create a second move.
- Finished matches reject further moves.
- Queue cancellation and pairing cannot assign a player twice.
- Unauthorized users cannot read or modify another match.
- Completed results save once.
- Reconnecting restores the authoritative match state.

## 10. Implementation Order

1. Game engine and automated rule tests.
2. Guest authentication and database permissions.
3. Private-room creation, joining, and readiness.
4. Server-validated Classic gameplay and synchronization.
5. Reconnect handling, Blitz, and timers.
6. Quick Match queue.
7. Interface polish, history, and integration testing.
8. Architecture documentation, deployment, and release.

## 11. Development Process

- Use Scrum planning, reviews, and retrospectives.
- Rotate project roles between team members.
- Track tasks and acceptance criteria in Trello.
- Use GitHub branches and pull requests.
- Run automated tests before merging.
- Record actual completed work and known limitations.
- Prepare release instructions and a maintenance schedule.

## 12. Scope Limits

- No real-money betting or payments.
- No spectators, tournaments, or ranked ladder in the first release.
- Development starts locally without paid hosting.
- Security and multiplayer behavior require implementation and
  testing before the application is described as release-ready.
