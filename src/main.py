from __future__ import annotations

import sys

import pygame

from game_logic import (
    MAP_COLS,
    MAP_ROWS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILE_SIZE,
    Enemy,
    Loot,
    Player,
    Vec2,
    build_castle_map,
    clamp,
    collect_nearby_loot,
    resolve_player_aoe_attack,
    resolve_player_attack,
    spawn_enemy_around_player,
    update_enemies,
)

ISO_Y = 0.58


def world_to_screen(world: Vec2, camera: Vec2) -> tuple[int, int]:
    return int(world.x - camera.x), int((world.y - camera.y) * ISO_Y)


def draw_text(surface: pygame.Surface, text: str, pos: tuple[int, int], color: tuple[int, int, int], font: pygame.font.Font) -> None:
    surface.blit(font.render(text, True, color), pos)


def make_player_sprite() -> pygame.Surface:
    surf = pygame.Surface((48, 64), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (0, 0, 0, 95), (10, 48, 28, 10))
    pygame.draw.rect(surf, (39, 50, 78), (14, 30, 20, 20), border_radius=4)
    pygame.draw.circle(surf, (202, 174, 150), (24, 24), 9)
    pygame.draw.rect(surf, (88, 127, 195), (10, 34, 8, 15), border_radius=3)
    pygame.draw.rect(surf, (88, 127, 195), (30, 34, 8, 15), border_radius=3)
    pygame.draw.rect(surf, (160, 182, 218), (22, 36, 4, 16))
    return surf


def make_enemy_sprite() -> pygame.Surface:
    surf = pygame.Surface((44, 58), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (0, 0, 0, 95), (8, 44, 28, 10))
    pygame.draw.polygon(surf, (109, 34, 40), [(22, 6), (35, 18), (29, 44), (15, 44), (9, 18)])
    pygame.draw.circle(surf, (189, 77, 77), (16, 20), 3)
    pygame.draw.circle(surf, (189, 77, 77), (28, 20), 3)
    return surf


def draw_castle_map(screen: pygame.Surface, camera: Vec2, castle_map: list[list[int]]) -> None:
    screen.fill((16, 17, 23))
    for y in range(MAP_ROWS):
        for x in range(MAP_COLS):
            wx = x * TILE_SIZE + TILE_SIZE / 2
            wy = y * TILE_SIZE + TILE_SIZE / 2
            sx, sy = world_to_screen(Vec2(wx, wy), camera)
            if sx < -TILE_SIZE or sy < -TILE_SIZE or sx > SCREEN_WIDTH + TILE_SIZE or sy > SCREEN_HEIGHT + TILE_SIZE:
                continue
            if castle_map[y][x] == 0:
                color = (41, 45, 58) if (x + y) % 2 == 0 else (34, 37, 48)
                pygame.draw.rect(screen, color, (sx - TILE_SIZE // 2, sy - int(TILE_SIZE * ISO_Y / 2), TILE_SIZE, int(TILE_SIZE * ISO_Y)))
            else:
                pygame.draw.rect(screen, (74, 76, 86), (sx - TILE_SIZE // 2, sy - int(TILE_SIZE * ISO_Y), TILE_SIZE, int(TILE_SIZE * ISO_Y)))
                pygame.draw.rect(screen, (94, 96, 108), (sx - TILE_SIZE // 2, sy - int(TILE_SIZE * ISO_Y) - 18, TILE_SIZE, 18))


def draw_inventory_menu(screen: pygame.Surface, player: Player, selected_index: int, font: pygame.font.Font, title_font: pygame.font.Font) -> None:
    panel = pygame.Surface((700, 420), pygame.SRCALPHA)
    panel.fill((9, 10, 16, 228))
    screen.blit(panel, (290, 140))
    pygame.draw.rect(screen, (117, 124, 150), (290, 140, 700, 420), 2)

    draw_text(screen, "Inventory - Weapons", (315, 160), (230, 233, 245), title_font)
    draw_text(screen, "UP/DOWN select | ENTER equip | I close", (315, 188), (178, 184, 203), font)

    weapons = player.inventory.list_weapons()
    if not weapons:
        draw_text(screen, "No weapons found. Kill enemies for drops.", (320, 230), (204, 179, 165), font)
        return

    start_y = 224
    for idx, weapon in enumerate(weapons):
        is_selected = idx == selected_index
        is_equipped = player.inventory.equipped_weapon is weapon
        name_color = (244, 226, 164) if is_equipped else (214, 219, 236)
        if is_selected:
            pygame.draw.rect(screen, (43, 55, 86), (315, start_y + idx * 30 - 3, 320, 26), border_radius=4)
        mark = "[E]" if is_equipped else "   "
        draw_text(screen, f"{mark} {weapon.name}", (322, start_y + idx * 30), name_color, font)

    weapon = weapons[selected_index]
    box_x = 650
    pygame.draw.rect(screen, (26, 29, 40), (box_x, 224, 320, 290), border_radius=6)
    pygame.draw.rect(screen, weapon.color, (box_x + 20, 250, 16, 56), border_radius=3)
    draw_text(screen, "Selected Weapon", (box_x + 48, 234), (219, 223, 235), font)
    draw_text(screen, weapon.name, (box_x + 48, 262), (241, 227, 178), title_font)
    draw_text(screen, f"Damage bonus: +{weapon.damage_bonus}", (box_x + 48, 296), (214, 220, 232), font)
    draw_text(screen, f"Required level: {weapon.required_level}", (box_x + 48, 324), (214, 220, 232), font)
    draw_text(screen, f"Speed rating: {weapon.speed_rating}/10", (box_x + 48, 352), (214, 220, 232), font)

    can_equip = player.level >= weapon.required_level
    color = (120, 214, 150) if can_equip else (214, 120, 120)
    text = "Can equip" if can_equip else "Level too low"
    draw_text(screen, text, (box_x + 48, 384), color, font)


def draw_scene(
    screen: pygame.Surface,
    player: Player,
    enemies: list[Enemy],
    loot_items: list[Loot],
    camera: Vec2,
    font: pygame.font.Font,
    castle_map: list[list[int]],
    player_sprite: pygame.Surface,
    enemy_sprite: pygame.Surface,
    inventory_open: bool,
    selected_weapon_index: int,
) -> None:
    draw_castle_map(screen, camera, castle_map)

    for loot in loot_items:
        lx, ly = world_to_screen(loot.pos, camera)
        pygame.draw.circle(screen, (212, 171, 54), (lx, ly), 5)
        if loot.weapon:
            pygame.draw.rect(screen, loot.weapon.color, (lx - 3, ly - 14, 6, 10))
        elif loot.potion:
            pygame.draw.circle(screen, (180, 57, 79), (lx, ly - 10), 4)

    for enemy in sorted([e for e in enemies if e.is_alive], key=lambda e: e.pos.y):
        ex, ey = world_to_screen(enemy.pos, camera)
        screen.blit(enemy_sprite, (ex - 22, ey - 50))
        hp_ratio = max(0, enemy.hp / enemy.max_hp)
        pygame.draw.rect(screen, (40, 12, 12), (ex - 18, ey - 26, 36, 5))
        pygame.draw.rect(screen, (226, 62, 62), (ex - 18, ey - 26, int(36 * hp_ratio), 5))

    px, py = world_to_screen(player.pos, camera)
    screen.blit(player_sprite, (px - 24, py - 56))

    hp_ratio = max(0, player.hp / player.max_hp)
    xp_ratio = player.xp / player.next_level_xp if player.next_level_xp else 0
    aoe_cd_left = max(0.0, player.aoe_timer)

    pygame.draw.rect(screen, (45, 18, 18), (12, 12, 290, 18))
    pygame.draw.rect(screen, (220, 70, 70), (12, 12, int(290 * hp_ratio), 18))
    pygame.draw.rect(screen, (16, 24, 42), (12, 36, 290, 12))
    pygame.draw.rect(screen, (74, 110, 231), (12, 36, int(290 * xp_ratio), 12))

    draw_text(screen, f"HP: {player.hp}/{player.max_hp}", (318, 9), (232, 236, 244), font)
    draw_text(screen, f"LVL: {player.level}", (12, 54), (232, 236, 244), font)
    draw_text(screen, f"Gold: {player.gold}", (92, 54), (220, 194, 118), font)
    draw_text(screen, f"DMG: {player.damage}", (210, 54), (214, 220, 230), font)
    draw_text(screen, f"AOE DMG: {player.aoe_damage}", (12, 74), (206, 212, 233), font)
    draw_text(screen, f"AOE Radius: {player.aoe_radius}", (140, 74), (206, 212, 233), font)
    draw_text(screen, f"AOE CD: {aoe_cd_left:.1f}s", (288, 74), (206, 212, 233), font)
    draw_text(screen, f"Inventory: {len(player.inventory.items)}/{player.inventory.max_slots}", (12, 94), (210, 214, 223), font)
    weapon = player.inventory.equipped_weapon.name if player.inventory.equipped_weapon else "Bare hands"
    draw_text(screen, f"Weapon: {weapon}", (12, 114), (170, 186, 224), font)
    draw_text(screen, "WASD move | SPACE melee | E AOE burst | I inventory | Q potion | R restart | ESC quit", (12, SCREEN_HEIGHT - 28), (200, 205, 214), font)

    if inventory_open:
        draw_inventory_menu(screen, player, selected_weapon_index, font, pygame.font.SysFont("segoeui", 22, bold=True))


def reset_game_state() -> tuple[Player, list[Enemy], list[Loot], list[list[int]], bool, float, bool, int]:
    player = Player()
    enemies: list[Enemy] = []
    loot_items: list[Loot] = []
    castle_map = build_castle_map()
    game_over = False
    spawn_timer = 0.0
    inventory_open = False
    selected_weapon_index = 0
    return player, enemies, loot_items, castle_map, game_over, spawn_timer, inventory_open, selected_weapon_index


def run() -> None:
    pygame.init()
    pygame.display.set_caption("Darkstone Keep - 2.5D action RPG")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("segoeui", 18)

    player, enemies, loot_items, castle_map, game_over, spawn_timer, inventory_open, selected_weapon_index = reset_game_state()
    player_sprite = make_player_sprite()
    enemy_sprite = make_enemy_sprite()

    while True:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                if event.key == pygame.K_r and game_over:
                    player, enemies, loot_items, castle_map, game_over, spawn_timer, inventory_open, selected_weapon_index = reset_game_state()

                if not game_over:
                    if event.key == pygame.K_i:
                        inventory_open = not inventory_open
                        selected_weapon_index = 0
                    elif event.key == pygame.K_q and not inventory_open:
                        potion = player.inventory.consume_potion()
                        if potion:
                            player.hp = int(clamp(player.hp + potion.heal_amount, 0, player.max_hp))
                    elif event.key == pygame.K_SPACE and not inventory_open:
                        loot_items.extend(resolve_player_attack(player, enemies))
                    elif event.key == pygame.K_e and not inventory_open:
                        loot_items.extend(resolve_player_aoe_attack(player, enemies))
                    elif inventory_open:
                        weapons = player.inventory.list_weapons()
                        if weapons and event.key == pygame.K_UP:
                            selected_weapon_index = (selected_weapon_index - 1) % len(weapons)
                        elif weapons and event.key == pygame.K_DOWN:
                            selected_weapon_index = (selected_weapon_index + 1) % len(weapons)
                        elif weapons and event.key == pygame.K_RETURN:
                            weapon = weapons[selected_weapon_index]
                            if player.level >= weapon.required_level:
                                player.inventory.equip_weapon_by_index(selected_weapon_index)

        if not game_over:
            if not inventory_open:
                keys = pygame.key.get_pressed()
                dx = float(keys[pygame.K_d]) - float(keys[pygame.K_a])
                dy = float(keys[pygame.K_s]) - float(keys[pygame.K_w])
                player.move(dx, dy, dt)

            player.update(dt)
            spawn_timer += dt
            if spawn_timer >= 1.05 and len([e for e in enemies if e.is_alive]) < 22:
                spawn_timer = 0
                enemies.append(spawn_enemy_around_player(player.pos, player.level))

            incoming_damage = update_enemies(player, enemies, dt)
            if incoming_damage:
                player.hp = int(clamp(player.hp - incoming_damage, 0, player.max_hp))

            collect_nearby_loot(player, loot_items)
            if player.hp <= 0:
                game_over = True

        camera = Vec2(player.pos.x - SCREEN_WIDTH / 2, player.pos.y - (SCREEN_HEIGHT / 2) / ISO_Y)
        draw_scene(
            screen,
            player,
            enemies,
            loot_items,
            camera,
            font,
            castle_map,
            player_sprite,
            enemy_sprite,
            inventory_open,
            selected_weapon_index,
        )

        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            draw_text(screen, "You died in the castle ruins. Press R to restart or ESC to quit.", (SCREEN_WIDTH // 2 - 280, SCREEN_HEIGHT // 2), (244, 229, 191), font)

        pygame.display.flip()


if __name__ == "__main__":
    run()
