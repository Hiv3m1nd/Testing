# Darkstone Keep (Diablo-style starter clone)

I built this so you can run and package a simple Diablo-like action RPG on Windows with almost no setup.

## What this is

A small top-down hack-and-slash prototype inspired by Diablo 2:
- WASD movement
- Space to attack nearby enemies
- Enemies chase and attack
- Loot drops as gold
- XP + level-ups with stat growth
- "Game over" screen when HP reaches zero

This is **not a full Diablo 2 remake** (that would require a massive team and years), but this is a working foundation you can install and play.

## 1) Install Python (one time)

- Download Python 3.11+ from: https://www.python.org/downloads/windows/
- During install, check **"Add Python to PATH"**.

## 2) Run the game on Windows

1. Open this project folder.
2. Double-click `run_game.bat`.

That script installs dependencies and launches the game.

## 3) Build an installable-style EXE

1. Double-click `build_windows_exe.bat`.
2. Wait for build completion.
3. Your app will be at: `dist/DarkstoneKeep.exe`

You can zip the `dist` folder and share the executable.

## Controls

- `W A S D` = move
- `SPACE` = attack
- `ESC` = quit

## Project files

- `src/main.py` - game loop + rendering
- `src/game_logic.py` - gameplay systems
- `tests/test_game_logic.py` - logic tests
- `run_game.bat` - run on Windows
- `build_windows_exe.bat` - package to EXE

## Next upgrades (if you want me to keep going)

- Character classes and skill tree
- Inventory and item rarity system
- Procedural dungeons
- Bosses and quests
- Sound effects + music
- Better art + animation
