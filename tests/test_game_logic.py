from src.game_logic import Enemy, Player, Vec2, collect_nearby_loot, resolve_player_attack, update_enemies


def test_player_levels_up_from_xp() -> None:
    player = Player()
    leveled = player.gain_xp(150)
    assert leveled is True
    assert player.level == 2
    assert player.hp == player.max_hp


def test_attack_kills_enemy_and_drops_loot() -> None:
    player = Player()
    enemy = Enemy(Vec2(player.pos.x + 10, player.pos.y + 10), level=1)
    enemy.hp = 1

    loot = resolve_player_attack(player, [enemy])
    assert enemy.hp <= 0
    assert len(loot) == 1
    assert loot[0].gold >= 8


def test_enemy_damages_player_when_in_range() -> None:
    player = Player()
    enemy = Enemy(Vec2(player.pos.x, player.pos.y), level=1)
    enemy.attack_timer = 0

    damage = update_enemies(player, [enemy], dt=0.016)
    assert damage > 0


def test_collects_nearby_loot() -> None:
    player = Player()
    drops = [
        type("Loot", (), {"pos": Vec2(player.pos.x, player.pos.y), "gold": 12})(),
        type("Loot", (), {"pos": Vec2(player.pos.x + 500, player.pos.y + 500), "gold": 99})(),
    ]
    total = collect_nearby_loot(player, drops)
    assert total == 12
    assert player.gold == 12
    assert len(drops) == 1
