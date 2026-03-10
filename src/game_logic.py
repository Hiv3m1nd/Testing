from __future__ import annotations

import math
import random
from dataclasses import dataclass

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WORLD_WIDTH = 2200
WORLD_HEIGHT = 2200
TILE_SIZE = 80
MAP_COLS = WORLD_WIDTH // TILE_SIZE
MAP_ROWS = WORLD_HEIGHT // TILE_SIZE


@dataclass
class Vec2:
    x: float
    y: float

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)

    def distance_to(self, other: "Vec2") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)


@dataclass
class Weapon:
    name: str
    damage_bonus: int
    required_level: int
    speed_rating: int
    color: tuple[int, int, int]


@dataclass
class Potion:
    heal_amount: int


@dataclass
class Loot:
    pos: Vec2
    gold: int = 0
    weapon: Weapon | None = None
    potion: Potion | None = None


class Inventory:
    def __init__(self, max_slots: int = 8) -> None:
        self.max_slots = max_slots
        self.items: list[Weapon | Potion] = []
        self.equipped_weapon: Weapon | None = None

    def has_space(self) -> bool:
        return len(self.items) < self.max_slots

    def add_item(self, item: Weapon | Potion) -> bool:
        if not self.has_space():
            return False
        self.items.append(item)
        if isinstance(item, Weapon) and (self.equipped_weapon is None or item.damage_bonus > self.equipped_weapon.damage_bonus):
            self.equipped_weapon = item
        return True

    def consume_potion(self) -> Potion | None:
        for idx, item in enumerate(self.items):
            if isinstance(item, Potion):
                return self.items.pop(idx)
        return None

    def list_weapons(self) -> list[Weapon]:
        return [item for item in self.items if isinstance(item, Weapon)]

    def equip_weapon_by_index(self, weapon_index: int) -> bool:
        weapons = self.list_weapons()
        if 0 <= weapon_index < len(weapons):
            self.equipped_weapon = weapons[weapon_index]
            return True
        return False


class Player:
    def __init__(self) -> None:
        self.pos = Vec2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
        self.speed = 220.0
        self.radius = 16
        self.max_hp = 120
        self.hp = self.max_hp

        self.base_damage = 18
        self.attack_range = 58
        self.attack_cooldown = 0.36
        self.attack_timer = 0.0
        self.attack_anim_timer = 0.0

        self.aoe_base_damage = 12
        self.aoe_radius = 115
        self.aoe_cooldown = 3.8
        self.aoe_timer = 0.0
        self.aoe_anim_timer = 0.0

        self.gold = 0
        self.level = 1
        self.xp = 0
        self.next_level_xp = 120
        self.inventory = Inventory(max_slots=8)

    @property
    def damage(self) -> int:
        bonus = self.inventory.equipped_weapon.damage_bonus if self.inventory.equipped_weapon else 0
        return self.base_damage + bonus

    @property
    def aoe_damage(self) -> int:
        bonus = 0
        if self.inventory.equipped_weapon:
            bonus = max(1, self.inventory.equipped_weapon.damage_bonus // 2)
        return self.aoe_base_damage + bonus

    def move(self, dx: float, dy: float, dt: float) -> None:
        length = math.hypot(dx, dy)
        if length > 0:
            dx /= length
            dy /= length
        self.pos.x = clamp(self.pos.x + dx * self.speed * dt, 40, WORLD_WIDTH - 40)
        self.pos.y = clamp(self.pos.y + dy * self.speed * dt, 40, WORLD_HEIGHT - 40)

    def can_attack(self) -> bool:
        return self.attack_timer <= 0

    def can_aoe_attack(self) -> bool:
        return self.aoe_timer <= 0

    def update(self, dt: float) -> None:
        if self.attack_timer > 0:
            self.attack_timer -= dt
        if self.aoe_timer > 0:
            self.aoe_timer -= dt
        if self.attack_anim_timer > 0:
            self.attack_anim_timer -= dt
        if self.aoe_anim_timer > 0:
            self.aoe_anim_timer -= dt

    def gain_xp(self, amount: int) -> bool:
        self.xp += amount
        leveled_up = False
        while self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp
            self.level += 1
            self.next_level_xp = int(self.next_level_xp * 1.28)
            self.max_hp += 15
            self.base_damage += 3
            self.aoe_base_damage += 2
            self.aoe_radius += 8
            self.aoe_cooldown = max(1.8, self.aoe_cooldown - 0.12)
            leveled_up = True
        return leveled_up


class Enemy:
    def __init__(self, pos: Vec2, level: int) -> None:
        self.pos = pos
        self.radius = 14
        self.speed = 82 + (level * 6)
        self.max_hp = 42 + (level * 17)
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


def build_castle_map() -> list[list[int]]:
    grid = [[0 for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
    for y in range(MAP_ROWS):
        for x in range(MAP_COLS):
            if x in {0, 1, MAP_COLS - 1, MAP_COLS - 2} or y in {0, 1, MAP_ROWS - 1, MAP_ROWS - 2}:
                grid[y][x] = 1
            elif x % 7 == 0 and y % 5 != 0 and random.random() < 0.55:
                grid[y][x] = 1
            elif y % 6 == 0 and x % 4 != 0 and random.random() < 0.4:
                grid[y][x] = 1
    center = MAP_ROWS // 2
    for y in range(center - 2, center + 3):
        for x in range(center - 3, center + 4):
            grid[y][x] = 0
    return grid


def spawn_enemy_around_player(player_pos: Vec2, player_level: int) -> Enemy:
    angle = random.uniform(0, math.tau)
    distance = random.uniform(320, 620)
    pos = Vec2(
        clamp(player_pos.x + math.cos(angle) * distance, 64, WORLD_WIDTH - 64),
        clamp(player_pos.y + math.sin(angle) * distance, 64, WORLD_HEIGHT - 64),
    )
    level = max(1, player_level + random.choice([-1, 0, 0, 1]))
    return Enemy(pos, level)


def random_weapon(enemy_level: int) -> Weapon:
    names = ["Rust Blade", "Crypt Fang", "Night Reaver", "Bone Cleaver"]
    colors = [(151, 171, 187), (171, 125, 194), (194, 112, 112), (184, 184, 121)]
    idx = random.randrange(len(names))
    level_boost = max(1, enemy_level)
    return Weapon(
        name=names[idx],
        damage_bonus=2 + level_boost + random.randint(0, 3),
        required_level=max(1, level_boost - 1),
        speed_rating=random.randint(2, 7),
        color=colors[idx],
    )


def resolve_player_attack(player: Player, enemies: list[Enemy]) -> list[Loot]:
    loot_drops: list[Loot] = []
    if not player.can_attack():
        return loot_drops

    player.attack_timer = player.attack_cooldown
    player.attack_anim_timer = 0.16
    targets = [e for e in enemies if e.is_alive and e.pos.distance_to(player.pos) <= player.attack_range]
    for enemy in targets:
        enemy.hp -= player.damage
        if enemy.hp <= 0:
            player.gain_xp(enemy.xp_reward)
            drop = Loot(enemy.pos.copy(), gold=random.randint(6, 22))
            if random.random() < 0.30:
                drop.weapon = random_weapon(max(1, enemy.xp_reward // 30))
            else:
                drop.potion = Potion(heal_amount=random.randint(24, 45))
            loot_drops.append(drop)
    return loot_drops


def resolve_player_aoe_attack(player: Player, enemies: list[Enemy]) -> list[Loot]:
    loot_drops: list[Loot] = []
    if not player.can_aoe_attack():
        return loot_drops

    player.aoe_timer = player.aoe_cooldown
    player.aoe_anim_timer = 0.22
    targets = [e for e in enemies if e.is_alive and e.pos.distance_to(player.pos) <= player.aoe_radius]
    for enemy in targets:
        enemy.hp -= player.aoe_damage
        if enemy.hp <= 0:
            player.gain_xp(enemy.xp_reward)
            drop = Loot(enemy.pos.copy(), gold=random.randint(4, 16))
            if random.random() < 0.20:
                drop.weapon = random_weapon(max(1, enemy.xp_reward // 35))
            else:
                drop.potion = Potion(heal_amount=random.randint(20, 38))
            loot_drops.append(drop)
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
        elif enemy.attack_timer <= 0:
            incoming_damage += enemy.damage
            enemy.attack_timer = enemy.attack_cooldown

        if enemy.attack_timer > 0:
            enemy.attack_timer -= dt

    return incoming_damage


def collect_nearby_loot(player: Player, loot_items: list[Loot]) -> tuple[int, int]:
    collected_gold = 0
    collected_items = 0
    survivors: list[Loot] = []
    for loot in loot_items:
        if loot.pos.distance_to(player.pos) <= 32:
            player.gold += loot.gold
            collected_gold += loot.gold
            if loot.weapon and player.inventory.add_item(loot.weapon):
                collected_items += 1
            if loot.potion and player.inventory.add_item(loot.potion):
                collected_items += 1
        else:
            survivors.append(loot)
    loot_items[:] = survivors
    return collected_gold, collected_items
