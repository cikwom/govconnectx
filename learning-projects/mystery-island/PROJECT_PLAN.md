# Mystery Island — The Lost Lighthouse

> A beginner-friendly Python text-adventure project. This is a separate learning project and is not part of GovConnectX.

## Project goal

Build a complete command-line adventure in which a player wakes up on Mystery Island after a storm. The lighthouse is dark, the bridge is locked, and a rescue boat will arrive only if the player restores the beacon.

The project uses only the Python standard library. No web app, GUI, game engine, external database, or AI API is required.

## How we will learn

This project will be built incrementally with a mentor:

1. Learn a concept just before using it.
2. See a small, unrelated example.
3. Attempt a short exercise.
4. Apply the concept to the game in a small change.
5. Run the program and inspect the result.
6. Explain the code in the learner's own words before moving on.

The mentor should guide, review, and give hints rather than silently write the entire game. If the learner is stuck, explain the smallest next step and then work through the solution together.

## Required gameplay

- Show a title, introduction, and instructions.
- Ask for the player's name.
- Provide a menu that repeats until the player wins, loses, or quits.
- Include five locations: Beach, Jungle, Cave, Old Bridge, and Lighthouse.
- Track the player's name, current location, energy, inventory, and game outcome.
- Start with 5 energy points.
- Allow the player to collect a rope and lantern, each only once.
- Include at least three meaningful decisions with consequences.
- Require the rope to cross the Old Bridge.
- Require the lantern to restore the lighthouse beacon.
- Reject unexpected input without crashing or changing game state.
- End with a clear win, loss, or quit message.
- Offer replay with a completely fresh game state.

## Suggested project structure

```text
mystery-island/
├── main.py
├── game.py
├── tests/
│   └── test_game.py
├── README.md
└── .gitignore
```

- `main.py`: starts the game and handles command-line input/output.
- `game.py`: contains testable game state and game rules.
- `tests/test_game.py`: automated tests using `unittest`.
- `README.md`: setup, controls, rules, example playthroughs, and known limits.
- `.gitignore`: excludes virtual environments, bytecode, and generated local files.

## Learning roadmap and build checkpoints

### Phase 0 — Establish a baseline
Discuss variables, input strings, `print()` versus `return`, conditions, and why a menu needs a loop. Do not block progress because the learner cannot yet explain every term; revisit concepts as they appear in the build.

### Phase 1 — Python foundations
1. Variables, strings, integers, booleans, `print()`, `input()`, assignment, f-strings, and type conversion.
2. `if/elif/else`, comparisons, logical operators, and indentation.
3. `while` and `for` loops, counters, `break`, and `continue`.
4. Functions, parameters, return values, scope, and docstrings.
5. Lists, membership, dictionaries, and `.get()`.
6. Input validation with `.strip()` and `.lower()`; friendly error handling.
7. Basic `unittest` and Git habits.

### Phase 2 — Plan the game
Draw the route: Beach → Jungle → Cave → Old Bridge → Lighthouse. Decide which actions are possible at each location, where the rope and lantern are found, what consumes energy, and exactly how victory and defeat occur. Record deterministic rules in the README.

Suggested initial state:

```python
player = {
    "name": "Ada",
    "location": "Beach",
    "energy": 5,
    "inventory": [],
    "game_over": False,
    "won": False,
}
```

The implementation may differ if its design is explained. Energy must never become negative. Invalid or impossible actions must not consume energy. Define and test whether each legal move costs one energy point.

### Phase 3 — Build in small missions
- **Checkpoint A — One room:** show the Beach, a readable menu, and a working quit option. Invalid input must not crash.
- **Checkpoint B — Movement:** add Jungle and Cave; valid moves change location, invalid directions do not.
- **Checkpoint C — Inventory and puzzle:** add one-time rope and lantern pickups, inventory display, bridge lock, and lighthouse requirement.
- **Checkpoint D — Energy and outcomes:** add energy costs, loss at zero before rescue, victory after restoring the beacon with required items, and replay with fresh state.
- **Checkpoint E — Refactor:** keep game rules separate from interactive input/output so tests can call game functions directly.

### Phase 4 — Acceptance tests
Write at least eight meaningful automated tests; aim to cover all ten:

1. A new game starts at Beach with 5 energy and an empty inventory.
2. Invalid input leaves player state unchanged.
3. A legal move changes location and decreases energy exactly once.
4. An impossible move is rejected without energy cost.
5. Rope can be collected only once.
6. The bridge cannot be crossed without rope.
7. The lighthouse cannot be lit without the lantern.
8. The correct location and inventory can produce victory.
9. Energy exhaustion produces a loss.
10. Replay resets energy, location, inventory, and outcome flags.

Also check whitespace/case handling, energy never below zero, no actions after game over, and no victory from the wrong location.

Run tests with:

```bash
python -m unittest discover -s tests -v
```

### Phase 5 — Documentation and Git
Keep the repository clean and use meaningful commits and feature branches. Suggested commit messages:

- `feat: add the game introduction`
- `feat: implement player movement`
- `feat: add inventory and item gates`
- `fix: reject invalid actions without energy loss`
- `test: cover game outcomes and replay`

The README must explain prerequisites, how to run `python main.py`, controls, game rules, how to run tests, an example winning path, and known limitations.

### Phase 6 — Final demonstration and defence
Demonstrate:
- A complete winning playthrough.
- A losing playthrough.
- Invalid input followed by successful recovery.
- At least eight passing tests.

The learner should be able to explain:
- Why inventory is represented by a list.
- What condition stops the menu loop.
- A function that returns a value instead of printing.
- A bug fixed with help from a test.
- What was learned and independently verified.

## Definition of done

The project is complete when another beginner can obtain the repository, run `python main.py`, play a winning and losing path, recover from invalid commands, and run the automated tests successfully. The learner can explain the main functions and game rules without relying on a memorized script.

## Completion evidence

- Repository URL and final commit SHA.
- Python version and run instructions.
- Output from the full `unittest` command.
- README with rules and examples.
- Two short learning-log entries: topic → explanation → experiment → conclusion.
- A reflection beginning: “The concept I understand now that I didn't before is…”

## Scope and project boundaries

This is a local command-line learning game. Keep it separate from GovConnectX and other projects. Use the Python standard library and do not add external dependencies unless the scope is deliberately revised.
