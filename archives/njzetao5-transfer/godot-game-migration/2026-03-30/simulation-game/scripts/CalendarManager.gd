extends Control
class_name CalendarManager

## FM/NBA2k MyGM-style schedule w/custom events, training, card deck system

@export var calendar_view: RichTextLabel
@export var phone_events: VBoxContainer
@export var card_deck: HBoxContainer

enum ScheduleEvent { MATCH, TRAINING, MEETING, OPPORTUNITY }
var current_date: int = 0
var weekly_events: Array = []
var player_cards: Dictionary = {}  # player_id -> Array<Card>

class Card:
	var type: String  # 'passive', 'structure', 'tag'
	var name: String
	var effect: String  # ' +10% aim during clutch'
	var playstyle_tag: String  # 'aggressive', 'support'

func _ready():
	setup_calendar()
	generate_week_events()
	
func advance_day():
	current_date += 1
	update_calendar_view()
	resolve_events()
	
func setup_calendar():
	calendar_view.bbcode_text = "[center]Week %d - Day %d[/center]" % [current_date / 7, current_date % 7]

func generate_week_events():
	for day in 7:
		var event_type = randi() % ScheduleEvent.size()
		weekly_events.append({
			'day': day,
			'type': event_type,
			'name': _get_event_name(event_type),
			'description': _get_event_desc(event_type)
		})

func _get_event_name(type: int) -> String:
	match type:
		ScheduleEvent.MATCH: return "Scrim vs Rivals"
		ScheduleEvent.TRAINING: return "Aim Training"
		ScheduleEvent.MEETING: return "Team Strategy"
		ScheduleEvent.OPPORTUNITY: return "Sponsor Offer"

func resolve_training(player_id: int, focus: String):
	# Improve player card deck
	var new_card = Card.new()
	new_card.type = 'passive'
	new_card.name = '%s Focus' % focus.capitalize()
	new_card.effect = '+15 stats in %s' % focus
	new_card.playstyle_tag = focus
	player_cards[player_id].append(new_card)

func build_deck(player_id: int):
	# Deck for sim customization
	var deck = player_cards[player_id].slice(0, 5)  # Top 5 cards
	print("Deck for player %d: %s" % [player_id, deck])

# Phone notifications
func notify_event(event):
	var label = Label.new()
	label.text = "[%s] %s" % [event.name, event.description]
	phone_events.add_child(label)
