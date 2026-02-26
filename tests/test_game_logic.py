from src.game_logic import (
    Enemy,
    Player,
    Potion,
    Vec2,
    Weapon,
    build_castle_map,
    collect_nearby_loot,
    resolve_player_aoe_attack,
    resolve_player_attack,
    update_enemies,
)


def test_level_up_does_not_auto_heal_and_upgrades_aoe() -> None:
    player = Player()
    player.hp = 30
    start_aoe = player.aoe_radius
    leveled = player.gain_xp(150)
    assert leveled is True
    assert player.level == 2
    assert player.hp == 30
    assert player.aoe_radius > start_aoe


def test_attack_kills_enemy_and_always_drops_item_loot() -> None:
    player = Player()
    enemy = Enemy(Vec2(player.pos.x + 10, player.pos.y + 10), level=1)
    enemy.hp = 1
    loot = resolve_player_attack(player, [enemy])
    assert enemy.hp <= 0
    assert len(loot) == 1
    assert loot[0].gold >= 6
    assert (loot[0].weapon is not None) or (loot[0].potion is not None)


def test_aoe_attack_hits_multiple_enemies() -> None:
    player = Player()
    e1 = Enemy(Vec2(player.pos.x + 10, player.pos.y), level=1)
    e2 = Enemy(Vec2(player.pos.x + 20, player.pos.y + 10), level=1)
    e1.hp = 1
    e2.hp = 1
    loot = resolve_player_aoe_attack(player, [e1, e2])
    assert len(loot) == 2
    assert player.aoe_timer > 0


def test_enemy_damages_player_when_in_range() -> None:
    player = Player()
    enemy = Enemy(Vec2(player.pos.x, player.pos.y), level=1)
    enemy.attack_timer = 0
    damage = update_enemies(player, [enemy], dt=0.016)
    assert damage > 0


def test_collects_loot_and_respects_inventory_slots() -> None:
    player = Player()
    player.inventory.max_slots = 1
    drops = [
        type(
            "Loot",
            (),
            {
                "pos": Vec2(player.pos.x, player.pos.y),
                "gold": 12,
                "weapon": Weapon("X", 3, 1, 4, (0, 0, 0)),
                "potion": Potion(25),
            },
        )(),
    ]
    gold, items = collect_nearby_loot(player, drops)
    assert gold == 12
    assert items == 1
    assert len(player.inventory.items) == 1


def test_can_manually_swap_equipped_weapon() -> None:
    player = Player()
    weapon_a = Weapon("A", 3, 1, 4, (1, 2, 3))
    weapon_b = Weapon("B", 6, 1, 3, (4, 5, 6))
    player.inventory.add_item(weapon_a)
    player.inventory.add_item(weapon_b)

    player.inventory.equip_weapon_by_index(0)
    assert player.inventory.equipped_weapon is weapon_a


def test_castle_map_has_wall_borders() -> None:
    m = build_castle_map()
    assert all(cell == 1 for cell in m[0])
    assert all(row[0] == 1 for row in m)
