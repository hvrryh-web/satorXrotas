extends Control
class_name NJZCog

## TENET Dial Cog for NJZ aesthetic - SFX toggle, spinning glyphs

@export var glyph_font: Font
@export var spin_speed: float = 1.0
@export var sfx_on: AudioStreamPlayer
@export var sfx_off: AudioStreamPlayer

var glyphs: Array[String] = ['?', 'j', 'i', '!', '.', '•', 'I', 'l', 'L', 'r', 'R', 'P', 'p']
var current_index: int = 0
var is_spinning: bool = true
var sfx_enabled: bool = true

func _ready():
    size = Vector2(80, 80)
    position_central()
    start_spin()

func position_central():
    position = get_parent().size / 2 - size / 2

func _process(delta):
    if is_spinning:
        rotation_degrees += spin_speed * delta * 60

func toggle_sfx():
    sfx_enabled = not sfx_enabled
    if sfx_enabled:
        sfx_on.play()
    else:
        sfx_off.play()
    print('NJZ SFX: ', 'ON' if sfx_enabled else 'OFF')

func add_glyph_ring():
    # Draw spinning glyphs
    for i in glyphs.size():
        var angle = (i / float(glyphs.size())) * TAU
        var pos = Vector2(25).rotated(angle)
        draw_string(glyph_font, pos, glyphs[i], HORIZONTAL_ALIGNMENT_CENTER)
