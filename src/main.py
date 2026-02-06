from __future__ import annotations

import sys

import pygame

from game_logic import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    Enemy,
    Loot,
    Player,
    Vec2,
    clamp,
    collect_nearby_loot,
    resolve_player_attack,
    spawn_enemy_around_player,
    update_enemies,
)


def world_to_screen(world: Vec2, camera: Vec2) -> tuple[int, int]:
    return int(world.x - camera.x), int(world.y - camera.y)


def draw_text(surface: pygame.Surface, text: str, pos: tuple[int, int], color: tuple[int, int, int], font: pygame.font.Font) -> None:
    surface.blit(font.render(text, True, color), pos)


def draw_scene(
    screen: pygame.Surface,
    player: Player,
    enemies: list[Enemy],
    loot_items: list[Loot],
    camera: Vec2,
    font: pygame.font.Font,
) -> None:
    screen.fill((19, 22, 28))

    for gx in range(-32, SCREEN_WIDTH + 32, 32):
        pygame.draw.line(screen, (25, 29, 36), (gx, 0), (gx, SCREEN_HEIGHT), 1)
    for gy in range(-32, SCREEN_HEIGHT + 32, 32):
        pygame.draw.line(screen, (25, 29, 36), (0, gy), (SCREEN_WIDTH, gy), 1)

    for loot in loot_items:
        lx, ly = world_to_screen(loot.pos, camera)
        pygame.draw.circle(screen, (212, 171, 54), (lx, ly), 6)

    for enemy in enemies:
        if not enemy.is_alive:
            continue
        ex, ey = world_to_screen(enemy.pos, camera)
        pygame.draw.circle(screen, (173, 55, 55), (ex, ey), enemy.radius)
        hp_ratio = max(0, enemy.hp / enemy.max_hp)
        pygame.draw.rect(screen, (40, 12, 12), (ex - 18, ey - 22, 36, 5))
        pygame.draw.rect(screen, (226, 62, 62), (ex - 18, ey - 22, int(36 * hp_ratio), 5))

    px, py = world_to_screen(player.pos, camera)
    pygame.draw.circle(screen, (80, 151, 240), (px, py), player.radius)

    hp_ratio = max(0, player.hp / player.max_hp)
    xp_ratio = player.xp / player.next_level_xp if player.next_level_xp else 0

    pygame.draw.rect(screen, (45, 18, 18), (12, 12, 290, 18))
    pygame.draw.rect(screen, (220, 70, 70), (12, 12, int(290 * hp_ratio), 18))
    pygame.draw.rect(screen, (16, 24, 42), (12, 36, 290, 12))
    pygame.draw.rect(screen, (74, 110, 231), (12, 36, int(290 * xp_ratio), 12))

    draw_text(screen, f"HP: {player.hp}/{player.max_hp}", (318, 9), (232, 236, 244), font)
    draw_text(screen, f"Level: {player.level}", (12, 54), (232, 236, 244), font)
    draw_text(screen, f"Gold: {player.gold}", (108, 54), (220, 194, 118), font)
    draw_text(screen, "WASD move, SPACE attack, ESC quit", (12, SCREEN_HEIGHT - 28), (200, 205, 214), font)


def run() -> None:
    pygame.init()
    pygame.display.set_caption("Darkstone Keep - action RPG demo")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("segoeui", 18)

    player = Player()
    enemies: list[Enemy] = []
    loot_items: list[Loot] = []

    spawn_timer = 0.0
    game_over = False

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
                if event.key == pygame.K_SPACE and not game_over:
                    loot_items.extend(resolve_player_attack(player, enemies))

        if not game_over:
            keys = pygame.key.get_pressed()
            dx = float(keys[pygame.K_d]) - float(keys[pygame.K_a])
            dy = float(keys[pygame.K_s]) - float(keys[pygame.K_w])
            player.move(dx, dy, dt)
            player.update(dt)

            spawn_timer += dt
            if spawn_timer >= 1.1 and len([e for e in enemies if e.is_alive]) < 18:
                spawn_timer = 0
                enemies.append(spawn_enemy_around_player(player.pos, player.level))

            incoming_damage = update_enemies(player, enemies, dt)
            if incoming_damage:
                player.hp = int(clamp(player.hp - incoming_damage, 0, player.max_hp))

            collect_nearby_loot(player, loot_items)
            if player.hp <= 0:
                game_over = True

        camera = Vec2(player.pos.x - SCREEN_WIDTH / 2, player.pos.y - SCREEN_HEIGHT / 2)
        draw_scene(screen, player, enemies, loot_items, camera, font)

        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            screen.blit(overlay, (0, 0))
            draw_text(screen, "You have fallen. Press ESC to leave.", (SCREEN_WIDTH // 2 - 170, SCREEN_HEIGHT // 2), (244, 229, 191), font)

        pygame.display.flip()


if __name__ == "__main__":
    run()
