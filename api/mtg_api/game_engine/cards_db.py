"""
cards_db.py — Cartas implementadas com efeitos reais
Cada carta tem: id, name, mana_cost, cmc, type, subtypes,
power, toughness, keywords, abilities[], oracle_text
"""

CARDS = {
    # ═══════════════ CRIATURAS ═══════════════

    "llanowar_elves": {
        "id": "llanowar_elves",
        "name": "Llanowar Elves",
        "mana_cost": {"G": 1},
        "cmc": 1,
        "type": "Creature",
        "subtypes": ["Elf", "Druid"],
        "power": 1,
        "toughness": 1,
        "keywords": [],
        "color": "G",
        "image": "llanowar_elves",
        "oracle_text": "{T}: Add {G}.",
        "abilities": [
            {
                "type": "activated",
                "trigger": "tap",
                "cost": {"tap": True},
                "effect": "add_mana",
                "params": {"color": "G", "amount": 1}
            }
        ]
    },

    "grizzly_bears": {
        "id": "grizzly_bears",
        "name": "Grizzly Bears",
        "mana_cost": {"1": 1, "G": 1},
        "cmc": 2,
        "type": "Creature",
        "subtypes": ["Bear"],
        "power": 2,
        "toughness": 2,
        "keywords": [],
        "color": "G",
        "image": "grizzly_bears",
        "oracle_text": "",
        "abilities": []
    },

    "serra_angel": {
        "id": "serra_angel",
        "name": "Serra Angel",
        "mana_cost": {"3": 1, "W": 2},
        "cmc": 5,
        "type": "Creature",
        "subtypes": ["Angel"],
        "power": 4,
        "toughness": 4,
        "keywords": ["flying", "vigilance"],
        "color": "W",
        "image": "serra_angel",
        "oracle_text": "Flying, vigilance",
        "abilities": []
    },

    "lightning_bolt": {
        "id": "lightning_bolt",
        "name": "Lightning Bolt",
        "mana_cost": {"R": 1},
        "cmc": 1,
        "type": "Instant",
        "subtypes": [],
        "power": None,
        "toughness": None,
        "keywords": [],
        "color": "R",
        "image": "lightning_bolt",
        "oracle_text": "Lightning Bolt deals 3 damage to any target.",
        "abilities": [
            {
                "type": "spell",
                "effect": "deal_damage",
                "params": {"amount": 3, "target": "any"}
            }
        ]
    },

    "giant_growth": {
        "id": "giant_growth",
        "name": "Giant Growth",
        "mana_cost": {"G": 1},
        "cmc": 1,
        "type": "Instant",
        "subtypes": [],
        "power": None,
        "toughness": None,
        "keywords": [],
        "color": "G",
        "image": "giant_growth",
        "oracle_text": "Target creature gets +3/+3 until end of turn.",
        "abilities": [
            {
                "type": "spell",
                "effect": "pump_creature",
                "params": {"power": 3, "toughness": 3, "until_eot": True, "target": "creature"}
            }
        ]
    },

    "counterspell": {
        "id": "counterspell",
        "name": "Counterspell",
        "mana_cost": {"U": 2},
        "cmc": 2,
        "type": "Instant",
        "subtypes": [],
        "power": None,
        "toughness": None,
        "keywords": [],
        "color": "U",
        "image": "counterspell",
        "oracle_text": "Counter target spell.",
        "abilities": [
            {
                "type": "spell",
                "effect": "counter_spell",
                "params": {"target": "spell"}
            }
        ]
    },

    "doom_blade": {
        "id": "doom_blade",
        "name": "Doom Blade",
        "mana_cost": {"1": 1, "B": 1},
        "cmc": 2,
        "type": "Instant",
        "subtypes": [],
        "power": None,
        "toughness": None,
        "keywords": [],
        "color": "B",
        "image": "doom_blade",
        "oracle_text": "Destroy target nonblack creature.",
        "abilities": [
            {
                "type": "spell",
                "effect": "destroy_creature",
                "params": {"target": "creature", "restriction": "nonblack"}
            }
        ]
    },

    "forest": {
        "id": "forest",
        "name": "Forest",
        "mana_cost": {},
        "cmc": 0,
        "type": "Land",
        "subtypes": ["Forest"],
        "power": None,
        "toughness": None,
        "keywords": [],
        "color": None,
        "image": "forest",
        "oracle_text": "{T}: Add {G}.",
        "abilities": [
            {
                "type": "activated",
                "trigger": "tap",
                "cost": {"tap": True},
                "effect": "add_mana",
                "params": {"color": "G", "amount": 1}
            }
        ]
    },

    "mountain": {
        "id": "mountain",
        "name": "Mountain",
        "mana_cost": {},
        "cmc": 0,
        "type": "Land",
        "subtypes": ["Mountain"],
        "power": None,
        "toughness": None,
        "keywords": [],
        "color": None,
        "image": "mountain",
        "oracle_text": "{T}: Add {R}.",
        "abilities": [
            {
                "type": "activated",
                "trigger": "tap",
                "cost": {"tap": True},
                "effect": "add_mana",
                "params": {"color": "R", "amount": 1}
            }
        ]
    },

    "plains": {
        "id": "plains",
        "name": "Plains",
        "mana_cost": {},
        "cmc": 0,
        "type": "Land",
        "subtypes": ["Plains"],
        "power": None,
        "toughness": None,
        "keywords": [],
        "color": None,
        "image": "plains",
        "oracle_text": "{T}: Add {W}.",
        "abilities": [
            {
                "type": "activated",
                "trigger": "tap",
                "cost": {"tap": True},
                "effect": "add_mana",
                "params": {"color": "W", "amount": 1}
            }
        ]
    },

    "island": {
        "id": "island",
        "name": "Island",
        "mana_cost": {},
        "cmc": 0,
        "type": "Land",
        "subtypes": ["Island"],
        "power": None,
        "toughness": None,
        "keywords": [],
        "color": None,
        "image": "island",
        "oracle_text": "{T}: Add {U}.",
        "abilities": [
            {
                "type": "activated",
                "trigger": "tap",
                "cost": {"tap": True},
                "effect": "add_mana",
                "params": {"color": "U", "amount": 1}
            }
        ]
    },

    "swamp": {
        "id": "swamp",
        "name": "Swamp",
        "mana_cost": {},
        "cmc": 0,
        "type": "Land",
        "subtypes": ["Swamp"],
        "power": None,
        "toughness": None,
        "keywords": [],
        "color": None,
        "image": "swamp",
        "oracle_text": "{T}: Add {B}.",
        "abilities": [
            {
                "type": "activated",
                "trigger": "tap",
                "cost": {"tap": True},
                "effect": "add_mana",
                "params": {"color": "B", "amount": 1}
            }
        ]
    },

    "goblin_guide": {
        "id": "goblin_guide",
        "name": "Goblin Guide",
        "mana_cost": {"R": 1},
        "cmc": 1,
        "type": "Creature",
        "subtypes": ["Goblin", "Scout"],
        "power": 2,
        "toughness": 2,
        "keywords": ["haste"],
        "color": "R",
        "image": "goblin_guide",
        "oracle_text": "Haste\nWhenever Goblin Guide attacks, defending player reveals the top card of their library. If it's a land card, that player puts it into their hand.",
        "abilities": [
            {
                "type": "triggered",
                "trigger": "attacks",
                "effect": "goblin_guide_trigger",
                "params": {}
            }
        ]
    },

    "elvish_mystic": {
        "id": "elvish_mystic",
        "name": "Elvish Mystic",
        "mana_cost": {"G": 1},
        "cmc": 1,
        "type": "Creature",
        "subtypes": ["Elf", "Druid"],
        "power": 1,
        "toughness": 1,
        "keywords": [],
        "color": "G",
        "image": "elvish_mystic",
        "oracle_text": "{T}: Add {G}.",
        "abilities": [
            {
                "type": "activated",
                "trigger": "tap",
                "cost": {"tap": True},
                "effect": "add_mana",
                "params": {"color": "G", "amount": 1}
            }
        ]
    },

    "watchwolf": {
        "id": "watchwolf",
        "name": "Watchwolf",
        "mana_cost": {"G": 1, "W": 1},
        "cmc": 2,
        "type": "Creature",
        "subtypes": ["Wolf"],
        "power": 3,
        "toughness": 3,
        "keywords": [],
        "color": "GW",
        "image": "watchwolf",
        "oracle_text": "",
        "abilities": []
    },

    "savannah_lions": {
        "id": "savannah_lions",
        "name": "Savannah Lions",
        "mana_cost": {"W": 1},
        "cmc": 1,
        "type": "Creature",
        "subtypes": ["Cat"],
        "power": 2,
        "toughness": 1,
        "keywords": [],
        "color": "W",
        "image": "savannah_lions",
        "oracle_text": "",
        "abilities": []
    },

    "trained_armodon": {
        "id": "trained_armodon",
        "name": "Trained Armodon",
        "mana_cost": {"1": 1, "G": 2},
        "cmc": 3,
        "type": "Creature",
        "subtypes": ["Elephant"],
        "power": 3,
        "toughness": 3,
        "keywords": [],
        "color": "G",
        "image": "trained_armodon",
        "oracle_text": "",
        "abilities": []
    },

    "shock": {
        "id": "shock",
        "name": "Shock",
        "mana_cost": {"R": 1},
        "cmc": 1,
        "type": "Instant",
        "subtypes": [],
        "power": None,
        "toughness": None,
        "keywords": [],
        "color": "R",
        "image": "shock",
        "oracle_text": "Shock deals 2 damage to any target.",
        "abilities": [
            {
                "type": "spell",
                "effect": "deal_damage",
                "params": {"amount": 2, "target": "any"}
            }
        ]
    },

    "healing_salve": {
        "id": "healing_salve",
        "name": "Healing Salve",
        "mana_cost": {"W": 1},
        "cmc": 1,
        "type": "Instant",
        "subtypes": [],
        "power": None,
        "toughness": None,
        "keywords": [],
        "color": "W",
        "image": "healing_salve",
        "oracle_text": "Choose one — Target player gains 3 life; or prevent the next 3 damage that would be dealt to any target this turn.",
        "abilities": [
            {
                "type": "spell",
                "effect": "gain_life",
                "params": {"amount": 3, "target": "player"}
            }
        ]
    },

    "dark_ritual": {
        "id": "dark_ritual",
        "name": "Dark Ritual",
        "mana_cost": {"B": 1},
        "cmc": 1,
        "type": "Instant",
        "subtypes": [],
        "power": None,
        "toughness": None,
        "keywords": [],
        "color": "B",
        "image": "dark_ritual",
        "oracle_text": "Add {B}{B}{B}.",
        "abilities": [
            {
                "type": "spell",
                "effect": "add_mana",
                "params": {"color": "B", "amount": 3}
            }
        ]
    },

    "llanowar_sentinel": {
        "id": "llanowar_sentinel",
        "name": "Llanowar Sentinel",
        "mana_cost": {"2": 1, "G": 1},
        "cmc": 3,
        "type": "Creature",
        "subtypes": ["Elf"],
        "power": 2,
        "toughness": 4,
        "keywords": [],
        "color": "G",
        "image": "llanowar_sentinel",
        "oracle_text": "",
        "abilities": []
    },

    "craw_wurm": {
        "id": "craw_wurm",
        "name": "Craw Wurm",
        "mana_cost": {"4": 1, "G": 2},
        "cmc": 6,
        "type": "Creature",
        "subtypes": ["Wurm"],
        "power": 6,
        "toughness": 4,
        "keywords": [],
        "color": "G",
        "image": "craw_wurm",
        "oracle_text": "",
        "abilities": []
    },

    "prodigal_sorcerer": {
        "id": "prodigal_sorcerer",
        "name": "Prodigal Sorcerer",
        "mana_cost": {"2": 1, "U": 1},
        "cmc": 3,
        "type": "Creature",
        "subtypes": ["Human", "Wizard"],
        "power": 1,
        "toughness": 1,
        "keywords": [],
        "color": "U",
        "image": "prodigal_sorcerer",
        "oracle_text": "{T}: Prodigal Sorcerer deals 1 damage to any target.",
        "abilities": [
            {
                "type": "activated",
                "trigger": "tap",
                "cost": {"tap": True},
                "effect": "deal_damage",
                "params": {"amount": 1, "target": "any"}
            }
        ]
    },
}

# Decks pré-construídos
DECKS = {
    "red_aggro": {
        "name": "Chama Vermelha",
        "colors": ["R"],
        "cards": [
            "goblin_guide", "goblin_guide", "goblin_guide", "goblin_guide",
            "shock", "shock", "shock", "shock",
            "lightning_bolt", "lightning_bolt", "lightning_bolt", "lightning_bolt",
            "mountain", "mountain", "mountain", "mountain",
            "mountain", "mountain", "mountain", "mountain",
        ]
    },
    "green_stompy": {
        "name": "Floresta Selvagem",
        "colors": ["G"],
        "cards": [
            "llanowar_elves", "llanowar_elves", "llanowar_elves", "llanowar_elves",
            "elvish_mystic", "elvish_mystic", "elvish_mystic", "elvish_mystic",
            "grizzly_bears", "grizzly_bears", "grizzly_bears", "grizzly_bears",
            "trained_armodon", "trained_armodon", "trained_armodon",
            "giant_growth", "giant_growth", "giant_growth",
            "craw_wurm", "craw_wurm",
            "forest", "forest", "forest", "forest",
            "forest", "forest", "forest", "forest",
        ]
    },
    "white_weenie": {
        "name": "Legião Branca",
        "colors": ["W"],
        "cards": [
            "savannah_lions", "savannah_lions", "savannah_lions", "savannah_lions",
            "serra_angel", "serra_angel", "serra_angel",
            "healing_salve", "healing_salve", "healing_salve",
            "plains", "plains", "plains", "plains",
            "plains", "plains", "plains", "plains",
            "plains", "plains",
        ]
    },
    "blue_control": {
        "name": "Controle Azul",
        "colors": ["U"],
        "cards": [
            "counterspell", "counterspell", "counterspell", "counterspell",
            "prodigal_sorcerer", "prodigal_sorcerer", "prodigal_sorcerer",
            "island", "island", "island", "island",
            "island", "island", "island", "island",
            "island", "island", "island", "island",
        ]
    },
}
