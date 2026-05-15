extends Control
class_name HeroesManager

## 5 Heroes mascots (NJZ-inspired, fairy tale/religious themes)

var heroes = [
	{'name': 'Yahu', 'trait': 'Leader (Day)', 'story': 'Romulus strength', 'sprite_weight': 1.2},
	{'name': 'Meha', 'trait': 'Support (Night)', 'story': 'Remus wisdom', 'sprite_weight': 1.0},
	{'name': 'Rom', 'trait': 'Strategist (Twin Bind)', 'story': 'Evil binder', 'sprite_weight': 1.1},
	{'name': 'Rem', 'trait': 'Adapter (Fate Split)', 'story': 'Fate splitter', 'sprite_weight': 1.1},
	{'name': 'Fati', 'trait': 'Overcomer (Friends)', 'story': 'Group adventure', 'sprite_weight': 1.3}
]

func _ready():
	animate_heroes()

func animate_heroes():
	for i in heroes.size():
		var hero_node = get_node('Hero%d' % (i+1))
		var tween = create_tween()
		tween.tween_property(hero_node, 'modulate:a', 1.0, 1.0).from(0.0)
		tween.tween_property(hero_node, 'scale', Vector2(1.0, 1.0), 0.5)
		hero_node.sprite_weight = heroes[i].sprite_weight  # Physics modifier

func frame_grid():
	# Heroes frame quarterly grid + dial
	for hero in get_tree().get_nodes_in_group('heroes'):
		hero.z_index = 10  # Above panels
