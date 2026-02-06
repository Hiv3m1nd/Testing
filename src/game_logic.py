from __future__ import annotations

import math
import random
from dataclasses import dataclass

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WORLD_WIDTH = 2400
WORLD_HEIGHT = 2400


@dataclass
class Vec2:
    x: float
    y: float

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)

    def distance_to(self, other: "Vec2") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)


@dataclass
class Loot:
    pos: Vec2
    gold: int


class Player:
    def __init__(self) -> None:
        self.pos = Vec2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
        self.speed = 240.0
        self.radius = 16
        self.max_hp = 120
        self.hp = self.max_hp
        self.damage = 24
        self.attack_range = 48
        self.attack_cooldown = 0.35
        self.attack_timer = 0.0
        self.gold = 0
        self.level = 1
        self.xp = 0
        self.next_level_xp = 120

    def move(self, dx: float, dy: float, dt: float) -> None:
        length = math.hypot(dx, dy)
        if length > 0:
            dx /= length
            dy /= length
        self.pos.x = clamp(self.pos.x + dx * self.speed * dt, 0, WORLD_WIDTH)
        self.pos.y = clamp(self.pos.y + dy * self.speed * dt, 0, WORLD_HEIGHT)

    def can_attack(self) -> bool:
        return self.attack_timer <= 0

    def update(self, dt: float) -> None:
        if self.attack_timer > 0:
            self.attack_timer -= dt

    def gain_xp(self, amount: int) -> bool:
        self.xp += amount
        leveled_up = False
        while self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp
            self.level += 1
            self.next_level_xp = int(self.next_level_xp * 1.3)
            self.max_hp += 18
            self.hp = self.max_hp
            self.damage += 4
            leveled_up = True
        return leveled_up


class Enemy:
    def __init__(self, pos: Vec2, level: int) -> None:
        self.pos = pos
        self.radius = 14
        self.speed = 90 + (level * 5)
        self.max_hp = 46 + (level * 18)
        self.hp = self.max_hp
        self.damage = 8 + (level * 2)
        self.attack_range = 24
        self.attack_cooldown = 0.9
        self.attack_timer = random.uniform(0.0, 0.3)
        self.xp_reward = 30 + (level * 10)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def spawn_enemy_around_player(player_pos: Vec2, player_level: int) -> Enemy:
    angle = random.uniform(0, math.tau)
    distance = random.uniform(300, 640)
    pos = Vec2(
        clamp(player_pos.x + math.cos(angle) * distance, 24, WORLD_WIDTH - 24),
        clamp(player_pos.y + math.sin(angle) * distance, 24, WORLD_HEIGHT - 24),
    )
    level = max(1, player_level + random.choice([-1, 0, 0, 1]))
    return Enemy(pos, level)


def resolve_player_attack(player: Player, enemies: list[Enemy]) -> list[Loot]:
    loot_drops: list[Loot] = []
    if not player.can_attack():
        return loot_drops

    player.attack_timer = player.attack_cooldown
    targets = [e for e in enemies if e.is_alive and e.pos.distance_to(player.pos) <= player.attack_range]
    for enemy in targets:
        enemy.hp -= player.damage
        if enemy.hp <= 0:
            player.gain_xp(enemy.xp_reward)
            loot_drops.append(Loot(enemy.pos.copy(), gold=random.randint(8, 24)))
    return loot_drops


def update_enemies(player: Player, enemies: list[Enemy], dt: float) -> int:
    incoming_damage = 0
    for enemy in enemies:
        if not enemy.is_alive:
            continue

        distance = enemy.pos.distance_to(player.pos)
        if distance > enemy.attack_range:
            if distance > 0:
                dx = (player.pos.x - enemy.pos.x) / distance
                dy = (player.pos.y - enemy.pos.y) / distance
                enemy.pos.x += dx * enemy.speed * dt
                enemy.pos.y += dy * enemy.speed * dt
        else:
            if enemy.attack_timer <= 0:
                incoming_damage += enemy.damage
                enemy.attack_timer = enemy.attack_cooldown

        if enemy.attack_timer > 0:
            enemy.attack_timer -= dt

    return incoming_damage


def collect_nearby_loot(player: Player, loot_items: list[Loot]) -> int:
    collected = 0
    survivors: list[Loot] = []
    for loot in loot_items:
        if loot.pos.distance_to(player.pos) <= 28:
            player.gold += loot.gold
            collected += loot.gold
        else:
            survivors.append(loot)
    loot_items[:] = survivors
    return collected
