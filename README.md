# Darkstone Keep (Diablo-style 2.5D starter clone)

A top-down **2.5D-looking** action RPG starter inspired by Diablo 2, designed so beginners can run it on Windows.

## Features

- 2.5D-style rendering and depth-sorted characters
- Creepy castle-themed map with border walls
- Player/enemy sprites
- WASD movement + melee combat
- Secondary AOE burst attack that upgrades when leveling
- Enemy spawning, chasing, and attacking
- Gold + random item drops
- Limited-size inventory
- Inventory menu to inspect and swap weapons
- Random weapons (with attributes) and health potions
- Potions are consumed with `Q`
- Restart after death with `R`
- XP and leveling progression
- No automatic healing on kills/level-up

## Windows setup (easy)

1. Install Python 3.11+ from https://www.python.org/downloads/windows/
2. During install, check **Add Python to PATH**.

## Run the game

Double-click:

- `run_game.bat`

## Build an EXE

Double-click:

- `build_windows_exe.bat`

Built file:

- `dist/DarkstoneKeep.exe`

## Controls

- `W A S D` move
- `SPACE` melee attack
- `E` AOE burst
- `I` inventory menu
- `UP / DOWN` select weapon in menu
- `ENTER` equip selected weapon
- `Q` drink potion
- `R` restart after death
- `ESC` quit

## Files

- `src/main.py` rendering/game loop/sprites/UI
- `src/game_logic.py` combat, drops, inventory, map logic
- `tests/test_game_logic.py` automated tests
