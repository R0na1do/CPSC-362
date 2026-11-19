# Testing Classic game rules

These automated tests check `ClassicGame` in `game_engine.py`.
They use Python's built-in `unittest`, so no test packages, NiceGUI server,
database, or AWS connection are needed to run them.

## Run the tests

Open a terminal in the repository root (the folder containing `game_engine.py`).
With your Python environment activated, run:

```bash
python -B -m unittest discover -v
```

Without an activated environment, Linux/macOS users can use `python3` instead
of `python`. Windows users can use `py -3.12` instead.

- `-B` prevents Python from writing cache files.
- `-m unittest` starts Python's built-in test runner.
- `discover` finds the test files in `tests/`.
- `-v` displays each test's name and result.

Expected summary (execution time may vary):

```text
Ran 11 tests in ...

OK
```

The winning-line test includes 16 cases: eight winning lines for each player.
Other tests also use multiple cases, so 11 is the number of test methods,
not the total number of scenarios checked.

To run just the first test:

```bash
python -B -m unittest tests.test_game_engine.ClassicGameTests.test_new_game -v
```

## Coverage

- Empty board, X starting, and no initial result.
- Valid placements and alternating turns.
- Invalid types and out-of-range positions, with no state changes.
- Occupied cells rejected without state changes.
- Every winning row, column, and diagonal for both players.
- Full-board draws and a win on the ninth move.
- Moves rejected after a win or draw.
- Reset during play, after a win, and after a draw; play can restart.
- Separate games keep independent state.

## Understand the first test

`setUp()` creates a fresh game before each test method. `test_new_game()`
checks it using the shared `assert_fresh_game()` helper:

```python
self.assertEqual(self.game.board, [""] * 9)
self.assertEqual(self.game.current_player, "X")
self.assertIsNone(self.game.winner)
self.assertFalse(self.game.is_draw)
self.assertFalse(self.game.finished)
```

An assertion checks an expected result. For example, `assertEqual` fails if
the actual board differs from the expected nine empty strings.

`make_move()` returns two values: whether the move was accepted and a message.
The rejection tests check that the move is rejected, its message is nonempty,
and the board, turn, and result remain unchanged.

## Limits and manual checks

These tests verify the Python engine, not browser behavior or deployment.
The Classic engine tests workflow runs these tests on GitHub for pushes and pull requests. View results in the repository's Actions tab.

For a manual interface check, install the project dependencies and run
`python main.py`. Visit `http://127.0.0.1:8080`, start Classic with different
player names, play a win and a draw, try occupied cells, and use Play Again.
Check that the messages and board agree with the result, and test leaving
an unfinished round. Stop the server with Ctrl+C.

If a test fails, read its name and the expected/actual values before changing
the engine. Record the failure and investigate whether the code or test is
wrong; do not change an expected result just to make the test pass.
