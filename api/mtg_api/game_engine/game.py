"""
game.py — Motor de regras MTG
Implementa:
- Estrutura de turnos (Untap→Upkeep→Draw→Main1→Combat→Main2→End)
- Sistema de mana
- Stack com prioridade
- Combate completo (attackers, blockers, damage, first strike)
- State-based actions (SBA)
- Triggers (ETB, dies, attacks, blocks)
- Keywords: flying, vigilance, haste, trample, first strike, deathtouch, lifelink
- Efeitos until-end-of-turn
"""

import uuid
import random
import copy
from enum import Enum
from .cards_db import CARDS, DECKS


class Phase(Enum):
    UNTAP    = "untap"
    UPKEEP   = "upkeep"
    DRAW     = "draw"
    MAIN1    = "main1"
    COMBAT_BEGIN    = "combat_begin"
    COMBAT_ATTACKERS = "combat_attackers"
    COMBAT_BLOCKERS  = "combat_blockers"
    COMBAT_DAMAGE    = "combat_damage"
    COMBAT_END       = "combat_end"
    MAIN2    = "main2"
    END      = "end"
    CLEANUP  = "cleanup"


PHASE_ORDER = [
    Phase.UNTAP, Phase.UPKEEP, Phase.DRAW,
    Phase.MAIN1,
    Phase.COMBAT_BEGIN, Phase.COMBAT_ATTACKERS,
    Phase.COMBAT_BLOCKERS, Phase.COMBAT_DAMAGE, Phase.COMBAT_END,
    Phase.MAIN2, Phase.END, Phase.CLEANUP,
]


class Permanent:
    """Representa um permanente no battlefield."""
    def __init__(self, card_data, controller, owner):
        self.uid          = str(uuid.uuid4())[:8]
        self.card_id      = card_data["id"]
        self.name         = card_data["name"]
        self.type         = card_data["type"]
        self.subtypes     = card_data.get("subtypes", [])
        self.color        = card_data.get("color")
        self.keywords     = list(card_data.get("keywords", []))
        self.base_power   = card_data.get("power")
        self.base_tough   = card_data.get("toughness")
        self.abilities    = card_data.get("abilities", [])
        self.oracle_text  = card_data.get("oracle_text", "")
        self.controller   = controller  # player id
        self.owner        = owner
        self.tapped       = False
        self.damage       = 0           # damage marked on this permanent
        self.sick         = True        # summoning sickness
        self.attacking    = False
        self.blocking     = None        # uid of creature being blocked
        self.blocked_by   = []          # uids of blockers
        # Temporary effects (until end of turn)
        self.temp_power   = 0
        self.temp_tough   = 0
        self.temp_keywords = []

    @property
    def power(self):
        return (self.base_power or 0) + self.temp_power

    @property
    def toughness(self):
        return (self.base_tough or 0) + self.temp_tough

    @property
    def all_keywords(self):
        return set(self.keywords + self.temp_keywords)

    def can_attack(self):
        return (
            self.type == "Creature" and
            not self.tapped and
            not self.sick and
            "defender" not in self.all_keywords
        )

    def can_block(self):
        return self.type == "Creature" and not self.tapped

    def to_dict(self):
        return {
            "uid":         self.uid,
            "card_id":     self.card_id,
            "name":        self.name,
            "type":        self.type,
            "subtypes":    self.subtypes,
            "color":       self.color,
            "keywords":    list(self.all_keywords),
            "power":       self.power,
            "toughness":   self.toughness,
            "oracle_text": self.oracle_text,
            "controller":  self.controller,
            "tapped":      self.tapped,
            "damage":      self.damage,
            "sick":        self.sick,
            "attacking":   self.attacking,
            "blocking":    self.blocking,
            "blocked_by":  self.blocked_by,
            "can_attack":  self.can_attack(),
            "can_block":   self.can_block(),
        }


class StackItem:
    """Item na stack (feitiço ou habilidade)."""
    def __init__(self, item_type, source, controller, effect, params, targets=None):
        self.uid        = str(uuid.uuid4())[:8]
        self.item_type  = item_type   # "spell", "activated", "triggered"
        self.source     = source      # card_id ou permanent uid
        self.name       = params.get("name", source)
        self.controller = controller
        self.effect     = effect
        self.params     = params
        self.targets    = targets or []

    def to_dict(self):
        return {
            "uid":        self.uid,
            "item_type":  self.item_type,
            "source":     self.source,
            "name":       self.name,
            "controller": self.controller,
            "effect":     self.effect,
            "targets":    self.targets,
        }


class Player:
    def __init__(self, pid, name, deck_id):
        self.pid       = pid
        self.name      = name
        self.life      = 20
        self.mana_pool = {"W": 0, "U": 0, "B": 0, "R": 0, "G": 0, "C": 0}
        self.hand      = []   # list of card_ids
        self.library   = []   # list of card_ids
        self.graveyard = []
        self.land_played = False
        self.lost      = False
        self.won       = False
        self._build_deck(deck_id)

    def _build_deck(self, deck_id):
        deck_def = DECKS.get(deck_id, DECKS["green_stompy"])
        cards = list(deck_def["cards"])
        random.shuffle(cards)
        self.library = cards
        # Draw opening hand (7 cards)
        for _ in range(7):
            if self.library:
                self.hand.append(self.library.pop(0))

    def draw(self, n=1):
        drawn = []
        for _ in range(n):
            if not self.library:
                self.lost = True  # Rule 104.3c: draw from empty library
                return drawn
            card = self.library.pop(0)
            self.hand.append(card)
            drawn.append(card)
        return drawn

    def total_mana(self):
        return sum(self.mana_pool.values())

    def empty_mana(self):
        self.mana_pool = {"W": 0, "U": 0, "B": 0, "R": 0, "G": 0, "C": 0}

    def to_dict(self, hide_hand=False):
        return {
            "pid":         self.pid,
            "name":        self.name,
            "life":        self.life,
            "mana_pool":   self.mana_pool,
            "hand":        (["?"] * len(self.hand)) if hide_hand else self.hand,
            "hand_count":  len(self.hand),
            "library_count": len(self.library),
            "graveyard":   self.graveyard,
            "land_played": self.land_played,
            "lost":        self.lost,
            "won":         self.won,
        }


class GameEngine:
    """Motor principal do jogo."""

    def __init__(self, game_id, p1_name, p1_deck, p2_name, p2_deck):
        self.game_id    = game_id
        self.players    = {
            "p1": Player("p1", p1_name, p1_deck),
            "p2": Player("p2", p2_name, p2_deck),
        }
        self.active_player  = "p1"
        self.priority       = "p1"
        self.phase          = Phase.MAIN1
        self.turn           = 1
        self.stack          = []          # list of StackItem
        self.battlefield    = []          # list of Permanent
        self.log            = []
        self.waiting_action = None        # pending decision (attackers, blockers, targets)
        self.combat_attackers = []        # uids attacking
        self.combat_pairs   = {}          # blocker_uid -> attacker_uid
        self.eot_effects    = []          # effects to clear at cleanup

        # First turn: p1 doesn't draw (rule 103.8a)
        self._log("O jogo começou! Boa sorte!")
        self._log(f"Turno 1 — {self.players['p1'].name}")
        self._advance_to(Phase.MAIN1)

    # ══════════════════════════════════════
    #  TURN STRUCTURE
    # ══════════════════════════════════════

    def _advance_to(self, phase):
        self.phase = phase
        self._log(f"Fase: {phase.value}")

        if phase == Phase.UNTAP:
            self._do_untap()
            self._advance_to(Phase.UPKEEP)

        elif phase == Phase.UPKEEP:
            self._check_triggers("upkeep")

        elif phase == Phase.DRAW:
            if self.turn > 1 or self.active_player != "p1":
                drawn = self.players[self.active_player].draw()
                if drawn:
                    self._log(f"{self.players[self.active_player].name} comprou uma carta.")
            self._advance_to(Phase.MAIN1)

        elif phase == Phase.MAIN1:
            pass  # Player has priority, waits for actions

        elif phase == Phase.COMBAT_BEGIN:
            pass

        elif phase == Phase.COMBAT_ATTACKERS:
            self.waiting_action = "declare_attackers"

        elif phase == Phase.COMBAT_BLOCKERS:
            # AI auto-blocks if opponent's turn
            if self.active_player == "p1":
                self._ai_declare_blockers()
            else:
                self.waiting_action = "declare_blockers"

        elif phase == Phase.COMBAT_DAMAGE:
            self._resolve_combat_damage()
            self._advance_to(Phase.COMBAT_END)

        elif phase == Phase.COMBAT_END:
            self._end_combat()
            self._advance_to(Phase.MAIN2)

        elif phase == Phase.MAIN2:
            pass

        elif phase == Phase.END:
            self._check_triggers("end_step")
            self._advance_to(Phase.CLEANUP)

        elif phase == Phase.CLEANUP:
            self._do_cleanup()
            self._next_turn()

    def _do_untap(self):
        ap = self.active_player
        for perm in self.battlefield:
            if perm.controller == ap:
                perm.tapped = False
                perm.sick   = False  # summoning sickness clears on untap (rule 302.6)
        self.players[ap].land_played = False
        self._log(f"{self.players[ap].name} desentornou seus permanentes.")

    def _do_cleanup(self):
        ap = self.active_player
        # Clear end-of-turn effects
        for perm in self.battlefield:
            perm.temp_power    = 0
            perm.temp_tough    = 0
            perm.temp_keywords = []
        # Remove damage from creatures (rule 701.32)
        for perm in self.battlefield:
            perm.damage = 0
        # Empty mana pools
        for p in self.players.values():
            p.empty_mana()
        # Reset combat
        self.combat_attackers = []
        self.combat_pairs = {}
        for perm in self.battlefield:
            perm.attacking  = False
            perm.blocking   = None
            perm.blocked_by = []
        self.eot_effects = []

    def _next_turn(self):
        self.active_player = "p2" if self.active_player == "p1" else "p1"
        self.priority      = self.active_player
        self.turn         += 1
        name = self.players[self.active_player].name
        self._log(f"══ Turno {self.turn} — {name} ══")
        self._check_state_based_actions()
        self._advance_to(Phase.UNTAP)

    # ══════════════════════════════════════
    #  PLAYER ACTIONS
    # ══════════════════════════════════════

    def play_land(self, pid, card_id):
        """Rule 305: Play a land."""
        p = self.players[pid]
        errors = self._validate_action(pid)
        if errors: return self._err(errors)
        if self.phase not in (Phase.MAIN1, Phase.MAIN2):
            return self._err("Só pode jogar terrenos na fase principal.")
        if self.stack:
            return self._err("Não pode jogar terreno com itens na stack.")
        if p.land_played:
            return self._err("Você já jogou um terreno neste turno.")
        if card_id not in p.hand:
            return self._err("Carta não está na sua mão.")

        card = CARDS.get(card_id)
        if not card or card["type"] != "Land":
            return self._err("Não é um terreno.")

        p.hand.remove(card_id)
        p.land_played = True
        perm = Permanent(card, pid, pid)
        perm.sick = False  # Lands don't have summoning sickness
        self.battlefield.append(perm)
        self._log(f"{p.name} jogou {card['name']}.")
        self._check_triggers("enters_battlefield", perm)
        self._check_state_based_actions()
        return self._ok({"action": "land_played", "permanent": perm.to_dict()})

    def cast_spell(self, pid, card_id, targets=None):
        """Cast a spell from hand."""
        p = self.players[pid]
        errors = self._validate_action(pid)
        if errors: return self._err(errors)
        if card_id not in p.hand:
            return self._err("Carta não está na sua mão.")

        card = CARDS.get(card_id)
        if not card:
            return self._err("Carta inválida.")
        if card["type"] == "Land":
            return self._err("Use play_land para jogar terrenos.")

        # Sorcery speed check (rule 505.6a)
        is_sorcery_speed = card["type"] in ("Creature", "Enchantment", "Artifact", "Sorcery")
        if is_sorcery_speed:
            if self.phase not in (Phase.MAIN1, Phase.MAIN2):
                return self._err("Esse tipo de mágica só pode ser lançado na fase principal.")
            if self.stack:
                return self._err("Não pode lançar feitiços com itens na stack (velocidade de feitiço).")
            if pid != self.active_player:
                return self._err("Não é seu turno.")

        # Check mana cost
        cost_err = self._check_mana_cost(p, card["mana_cost"])
        if cost_err: return self._err(cost_err)

        # Pay mana
        self._pay_mana(p, card["mana_cost"])
        p.hand.remove(card_id)

        # Push to stack
        item = StackItem("spell", card_id, pid, card["abilities"][0]["effect"] if card.get("abilities") else "none",
                         {"name": card["name"], "card_id": card_id, "card": card},
                         targets or [])
        self.stack.append(item)
        self._log(f"{p.name} lançou {card['name']}.")
        self._check_state_based_actions()
        return self._ok({"action": "spell_cast", "stack_item": item.to_dict()})

    def activate_ability(self, pid, perm_uid, ability_index=0, targets=None):
        """Activate a permanent's activated ability."""
        perm = self._find_perm(perm_uid)
        if not perm:
            return self._err("Permanente não encontrado.")
        if perm.controller != pid:
            return self._err("Você não controla este permanente.")

        p = self.players[pid]
        abilities = [a for a in perm.abilities if a["type"] == "activated"]
        if ability_index >= len(abilities):
            return self._err("Habilidade inválida.")

        ab = abilities[ability_index]
        cost = ab.get("cost", {})

        # Check tap cost
        if cost.get("tap"):
            if perm.tapped:
                return self._err(f"{perm.name} já está virado.")
            if perm.sick and perm.type == "Creature":
                # Mana abilities don't have summoning sickness restriction (rule 302.6)
                if ab["effect"] != "add_mana":
                    return self._err(f"{perm.name} tem doença de invocação.")
            perm.tapped = True

        # Mana abilities resolve immediately (rule 605)
        if ab["effect"] == "add_mana":
            color = ab["params"]["color"]
            amount = ab["params"]["amount"]
            p.mana_pool[color] = p.mana_pool.get(color, 0) + amount
            self._log(f"{p.name} adicionou {''.join([f'{{{color}}}']*amount)} à sua reserva.")
            return self._ok({"action": "mana_added", "mana": p.mana_pool})

        # Other abilities go on the stack
        item = StackItem("activated", perm_uid, pid, ab["effect"],
                         {"name": f"{perm.name}: ability", **ab["params"]},
                         targets or [])
        self.stack.append(item)
        self._log(f"{p.name} ativou habilidade de {perm.name}.")
        return self._ok({"action": "ability_activated", "stack_item": item.to_dict()})

    def pass_priority(self, pid):
        """Pass priority. If both players pass with stack empty → advance phase."""
        if self.priority != pid:
            return self._err("Não é sua prioridade.")

        other = "p2" if pid == "p1" else "p1"

        if self.stack:
            # Resolve top of stack
            item = self.stack.pop()
            result = self._resolve_stack_item(item)
            self._check_state_based_actions()
            self.priority = self.active_player
            return self._ok({"action": "resolved", "resolved": item.to_dict(), **result})
        else:
            # Both passed with empty stack — advance phase
            next_phase = self._next_phase()
            if next_phase:
                self._advance_to(next_phase)
                self.priority = self.active_player
                return self._ok({"action": "phase_advanced", "phase": self.phase.value})
            return self._ok({"action": "waiting"})

    def declare_attackers(self, pid, attacker_uids):
        """Rule 508: Declare attackers step."""
        if pid != self.active_player:
            return self._err("Não é seu turno.")
        if self.phase != Phase.COMBAT_ATTACKERS:
            return self._err("Não estamos na etapa de declarar atacantes.")

        self.combat_attackers = []
        for uid in attacker_uids:
            perm = self._find_perm(uid)
            if not perm:
                return self._err(f"Permanente {uid} não encontrado.")
            if perm.controller != pid:
                return self._err(f"{perm.name} não é seu.")
            if not perm.can_attack():
                return self._err(f"{perm.name} não pode atacar.")

            perm.attacking = True
            # Tap unless vigilance (rule 508.1f)
            if "vigilance" not in perm.all_keywords:
                perm.tapped = True
            self.combat_attackers.append(uid)

        if self.combat_attackers:
            names = [self._find_perm(u).name for u in self.combat_attackers]
            defender = self.players["p2" if pid == "p1" else "p1"].name
            self._log(f"{self.players[pid].name} ataca com {', '.join(names)} → {defender}")
            # Check attack triggers
            for uid in self.combat_attackers:
                perm = self._find_perm(uid)
                self._check_triggers("attacks", perm)
        else:
            self._log(f"{self.players[pid].name} não ataca.")

        self.waiting_action = None
        # If AI's turn defending, auto-advance
        if self.active_player == "p1":
            self._advance_to(Phase.COMBAT_BLOCKERS)
        else:
            self._advance_to(Phase.COMBAT_BLOCKERS)

        return self._ok({"action": "attackers_declared", "attackers": self.combat_attackers})

    def declare_blockers(self, pid, block_assignments):
        """
        Rule 509: Declare blockers.
        block_assignments: {blocker_uid: attacker_uid}
        """
        if self.phase != Phase.COMBAT_BLOCKERS:
            return self._err("Não estamos na etapa de declarar bloqueadores.")

        defending_pid = "p2" if self.active_player == "p1" else "p1"
        if pid != defending_pid:
            return self._err("Não é você quem defende.")

        self.combat_pairs = {}
        for blocker_uid, attacker_uid in block_assignments.items():
            blocker = self._find_perm(blocker_uid)
            attacker = self._find_perm(attacker_uid)
            if not blocker or not attacker:
                return self._err("Permanente inválido.")
            if blocker.controller != pid:
                return self._err(f"{blocker.name} não é seu.")
            if not blocker.can_block():
                return self._err(f"{blocker.name} não pode bloquear.")
            if attacker_uid not in self.combat_attackers:
                return self._err(f"{attacker.name} não está atacando.")
            # Flying check (rule 702.9)
            if "flying" in attacker.all_keywords:
                if "flying" not in blocker.all_keywords and "reach" not in blocker.all_keywords:
                    return self._err(f"{blocker.name} não pode bloquear voadores.")

            blocker.blocking = attacker_uid
            attacker.blocked_by.append(blocker_uid)
            self.combat_pairs[blocker_uid] = attacker_uid

        if block_assignments:
            log_parts = [f"{self._find_perm(b).name} bloqueia {self._find_perm(a).name}"
                         for b, a in block_assignments.items()]
            self._log(f"{self.players[pid].name} bloqueia: {'; '.join(log_parts)}")
        else:
            self._log(f"{self.players[pid].name} não bloqueia.")

        self.waiting_action = None
        self._advance_to(Phase.COMBAT_DAMAGE)
        return self._ok({"action": "blockers_declared"})

    def resolve_stack(self, pid):
        """Manually resolve top of stack."""
        if not self.stack:
            return self._err("Stack vazia.")
        item = self.stack.pop()
        result = self._resolve_stack_item(item)
        self._check_state_based_actions()
        return self._ok({"action": "resolved", **result})

    def end_phase(self, pid):
        """Advance to next phase (shortcut)."""
        if pid != self.active_player:
            return self._err("Não é seu turno.")
        next_phase = self._next_phase()
        if next_phase:
            self._advance_to(next_phase)
            return self._ok({"action": "phase_advanced", "phase": self.phase.value})
        return self._ok({"action": "waiting"})

    # ══════════════════════════════════════
    #  STACK RESOLUTION
    # ══════════════════════════════════════

    def _resolve_stack_item(self, item):
        effect = item.effect
        params = item.params
        pid    = item.controller
        p      = self.players[pid]
        result = {}

        self._log(f"Resolvendo: {item.name}")

        if effect == "deal_damage":
            amount  = params.get("amount", 0)
            targets = item.targets
            for target in targets:
                self._deal_damage_to_target(target, amount, pid)
            result["damage"] = amount

        elif effect == "destroy_creature":
            targets = item.targets
            for t in targets:
                perm = self._find_perm(t)
                if perm and perm.type == "Creature":
                    restriction = params.get("restriction", "")
                    if restriction == "nonblack" and perm.color and "B" in perm.color:
                        self._log(f"{perm.name} é preta, não pode ser destruída.")
                        continue
                    if "indestructible" not in perm.all_keywords:
                        self._move_to_graveyard(perm)
                        result["destroyed"] = perm.name

        elif effect == "pump_creature":
            targets = item.targets
            for t in targets:
                perm = self._find_perm(t)
                if perm:
                    perm.temp_power += params.get("power", 0)
                    perm.temp_tough += params.get("toughness", 0)
                    self._log(f"{perm.name} fica +{params['power']}/+{params['toughness']} até o fim do turno.")
                    result["pumped"] = perm.name

        elif effect == "counter_spell":
            targets = item.targets
            for t in targets:
                # Find and remove from stack
                self.stack = [s for s in self.stack if s.uid != t]
                self._log(f"Feitiço countered!")
                # Return card to hand if it was a spell
                result["countered"] = t

        elif effect == "gain_life":
            targets = item.targets
            amount = params.get("amount", 0)
            for t in targets:
                if t in self.players:
                    self.players[t].life += amount
                    self._log(f"{self.players[t].name} ganha {amount} pontos de vida.")

        elif effect == "add_mana":
            color  = params.get("color", "C")
            amount = params.get("amount", 1)
            p.mana_pool[color] = p.mana_pool.get(color, 0) + amount
            self._log(f"Mana adicionada: {amount}{{{color}}}")

        elif effect == "none":
            # Permanent spell — put onto battlefield
            card = params.get("card")
            if card and card["type"] in ("Creature", "Artifact", "Enchantment"):
                perm = Permanent(card, pid, pid)
                self.battlefield.append(perm)
                self._log(f"{card['name']} entra no campo de batalha.")
                self._check_triggers("enters_battlefield", perm)
                result["permanent"] = perm.to_dict()

        elif effect == "goblin_guide_trigger":
            # Reveal top card of defending player's library
            defender_pid = "p2" if pid == "p1" else "p1"
            defender = self.players[defender_pid]
            if defender.library:
                top_card = defender.library[0]
                card_data = CARDS.get(top_card)
                self._log(f"Goblin Guide: {defender.name} revela {card_data['name'] if card_data else top_card}.")
                if card_data and card_data["type"] == "Land":
                    defender.library.pop(0)
                    defender.hand.append(top_card)
                    self._log(f"Era um terreno! {defender.name} coloca na mão.")

        return result

    # ══════════════════════════════════════
    #  COMBAT DAMAGE
    # ══════════════════════════════════════

    def _resolve_combat_damage(self):
        """Rule 510: Combat damage step."""
        if not self.combat_attackers:
            return

        defending_pid = "p2" if self.active_player == "p1" else "p1"
        defending_player = self.players[defending_pid]

        # First strike damage (rule 702.7)
        first_strikers = [uid for uid in self.combat_attackers
                          if "first strike" in (self._find_perm(uid).all_keywords if self._find_perm(uid) else set())
                          or "double strike" in (self._find_perm(uid).all_keywords if self._find_perm(uid) else set())]

        if first_strikers:
            self._assign_combat_damage(first_strikers, defending_pid, first_strike_only=True)
            self._check_state_based_actions()

        # Regular damage
        self._assign_combat_damage(self.combat_attackers, defending_pid, first_strike_only=False)
        self._check_state_based_actions()

    def _assign_combat_damage(self, attacker_uids, defending_pid, first_strike_only=False):
        defending_player = self.players[defending_pid]

        for uid in attacker_uids:
            attacker = self._find_perm(uid)
            if not attacker:
                continue

            is_first_striker = ("first strike" in attacker.all_keywords or
                                 "double strike" in attacker.all_keywords)
            if first_strike_only and not is_first_striker:
                continue
            if not first_strike_only and "first strike" in attacker.all_keywords and \
               "double strike" not in attacker.all_keywords:
                continue  # Already dealt first strike damage

            if attacker.blocked_by:
                # Assign damage to blockers
                remaining = attacker.power
                for blocker_uid in attacker.blocked_by:
                    blocker = self._find_perm(blocker_uid)
                    if not blocker or remaining <= 0:
                        continue
                    dmg = min(remaining, blocker.toughness - blocker.damage)
                    if "trample" in attacker.all_keywords:
                        dmg = blocker.toughness - blocker.damage
                    blocker.damage += dmg
                    remaining -= dmg
                    self._log(f"{attacker.name} causa {dmg} dano em {blocker.name}.")
                    # Lifelink
                    if "lifelink" in attacker.all_keywords:
                        self.players[attacker.controller].life += dmg
                        self._log(f"Lifelink: {self.players[attacker.controller].name} ganha {dmg} de vida.")

                # Trample: excess damage goes to player
                if "trample" in attacker.all_keywords and remaining > 0:
                    defending_player.life -= remaining
                    self._log(f"{attacker.name} causa {remaining} dano trampling em {defending_player.name}.")

            else:
                # Unblocked — deal damage to defending player
                dmg = attacker.power
                defending_player.life -= dmg
                self._log(f"{attacker.name} causa {dmg} dano em {defending_player.name} (não bloqueado).")
                if "lifelink" in attacker.all_keywords:
                    self.players[attacker.controller].life += dmg

        # Blocker damage to attackers
        for blocker_uid, attacker_uid in self.combat_pairs.items():
            blocker  = self._find_perm(blocker_uid)
            attacker = self._find_perm(attacker_uid)
            if not blocker or not attacker:
                continue
            is_first_striker = ("first strike" in blocker.all_keywords or
                                 "double strike" in blocker.all_keywords)
            if first_strike_only and not is_first_striker:
                continue
            if not first_strike_only and "first strike" in blocker.all_keywords and \
               "double strike" not in blocker.all_keywords:
                continue

            dmg = blocker.power
            attacker.damage += dmg
            self._log(f"{blocker.name} causa {dmg} dano em {attacker.name}.")
            if "lifelink" in blocker.all_keywords:
                self.players[blocker.controller].life += dmg

    def _end_combat(self):
        """Clean up combat state."""
        for uid in self.combat_attackers:
            perm = self._find_perm(uid)
            if perm:
                perm.attacking  = False
                perm.blocked_by = []
        for blocker_uid in self.combat_pairs:
            perm = self._find_perm(blocker_uid)
            if perm:
                perm.blocking = None
        self.combat_attackers = []
        self.combat_pairs     = {}

    # ══════════════════════════════════════
    #  STATE-BASED ACTIONS (Rule 704)
    # ══════════════════════════════════════

    def _check_state_based_actions(self):
        """Rule 704: Check and apply state-based actions continuously."""
        changed = True
        while changed:
            changed = False

            # 704.5a: Player with 0 or less life loses
            for p in self.players.values():
                if p.life <= 0 and not p.lost:
                    p.lost = True
                    self._log(f"{p.name} perdeu o jogo! (vida zerada)")
                    changed = True

            # 704.5b: Player with no library who draws loses
            for p in self.players.values():
                if p.lost and not p.won:
                    other_pid = "p2" if p.pid == "p1" else "p1"
                    self.players[other_pid].won = True
                    changed = True

            # 704.5f: Creature with toughness <= 0 goes to graveyard
            # 704.5g: Creature with damage >= toughness goes to graveyard
            to_remove = []
            for perm in self.battlefield:
                if perm.type == "Creature":
                    if perm.toughness <= 0:
                        to_remove.append(perm)
                        self._log(f"{perm.name} vai ao cemitério (resistência <= 0).")
                        changed = True
                    elif perm.damage >= perm.toughness:
                        if "indestructible" not in perm.all_keywords:
                            to_remove.append(perm)
                            self._log(f"{perm.name} vai ao cemitério (dano letal).")
                            changed = True
                        elif "deathtouch" in perm.all_keywords:
                            to_remove.append(perm)
                            self._log(f"{perm.name} destruído por deathtouch.")
                            changed = True

            for perm in to_remove:
                self._move_to_graveyard(perm)

    # ══════════════════════════════════════
    #  TRIGGERS
    # ══════════════════════════════════════

    def _check_triggers(self, event, source=None):
        """Check all permanents for triggered abilities matching event."""
        for perm in list(self.battlefield):
            for ab in perm.abilities:
                if ab["type"] != "triggered":
                    continue
                if ab["trigger"] == event or (event == "attacks" and ab["trigger"] == "attacks" and
                                               source and source.uid == perm.uid):
                    item = StackItem(
                        "triggered",
                        perm.uid,
                        perm.controller,
                        ab["effect"],
                        {"name": f"{perm.name} trigger", **ab.get("params", {})}
                    )
                    self.stack.append(item)
                    self._log(f"Trigger: {perm.name} — {ab['effect']}")

    # ══════════════════════════════════════
    #  AI (Simple)
    # ══════════════════════════════════════

    def _ai_take_turn(self):
        """Simple AI for p2."""
        pid = "p2"
        p   = self.players[pid]

        # Play lands
        for card_id in list(p.hand):
            card = CARDS.get(card_id)
            if card and card["type"] == "Land" and not p.land_played:
                self.play_land(pid, card_id)
                break

        # Tap lands for mana
        for perm in self.battlefield:
            if perm.controller == pid and perm.type == "Land" and not perm.tapped:
                self.activate_ability(pid, perm.uid)

        # Cast cheapest spell possible
        playable = []
        for card_id in p.hand:
            card = CARDS.get(card_id)
            if not card or card["type"] == "Land":
                continue
            if not self._check_mana_cost(p, card["mana_cost"]):
                playable.append((card["cmc"], card_id, card))

        playable.sort(key=lambda x: x[0])
        for _, card_id, card in playable:
            if card["type"] in ("Creature", "Sorcery", "Enchantment", "Artifact"):
                targets = self._ai_pick_targets(pid, card)
                self.cast_spell(pid, card_id, targets)

    def _ai_declare_blockers(self):
        """AI declares blockers for p2 when p1 attacks."""
        pid = "p2"
        assignments = {}
        attackers_sorted = sorted(
            [self._find_perm(u) for u in self.combat_attackers if self._find_perm(u)],
            key=lambda p: p.power, reverse=True
        )
        available_blockers = [p for p in self.battlefield
                              if p.controller == pid and p.can_block()]

        for attacker in attackers_sorted:
            for blocker in available_blockers:
                if blocker.uid in assignments:
                    continue
                if "flying" in attacker.all_keywords:
                    if "flying" not in blocker.all_keywords and "reach" not in blocker.all_keywords:
                        continue
                # Block if we can kill the attacker or save ourselves
                if blocker.power >= attacker.toughness or attacker.power >= self.players[pid].life:
                    assignments[blocker.uid] = attacker.uid
                    break

        self.declare_blockers(pid, assignments)

    def _ai_pick_targets(self, pid, card):
        """AI picks targets for spells."""
        targets = []
        opponent = "p1" if pid == "p2" else "p2"
        for ab in card.get("abilities", []):
            effect = ab.get("effect", "")
            params = ab.get("params", {})
            target_type = params.get("target", "")

            if target_type == "any":
                # Target opponent
                targets.append(opponent)
            elif target_type in ("creature", "any_target"):
                # Target opponent's strongest creature
                enemy_creatures = [p for p in self.battlefield
                                   if p.controller == opponent and p.type == "Creature"]
                if enemy_creatures:
                    targets.append(max(enemy_creatures, key=lambda c: c.power).uid)
                else:
                    targets.append(opponent)
        return targets

    # ══════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════

    def _next_phase(self):
        idx = PHASE_ORDER.index(self.phase)
        if idx + 1 < len(PHASE_ORDER):
            return PHASE_ORDER[idx + 1]
        return None

    def _find_perm(self, uid):
        for p in self.battlefield:
            if p.uid == uid:
                return p
        return None

    def _move_to_graveyard(self, perm):
        if perm in self.battlefield:
            self.battlefield.remove(perm)
            owner = self.players[perm.owner]
            owner.graveyard.append(perm.card_id)
            self._check_triggers("dies", perm)

    def _deal_damage_to_target(self, target, amount, source_pid):
        if target in self.players:
            self.players[target].life -= amount
            self._log(f"{self.players[source_pid].name} causa {amount} dano em {self.players[target].name}.")
        else:
            perm = self._find_perm(target)
            if perm:
                perm.damage += amount
                self._log(f"{amount} dano em {perm.name}.")
                if "deathtouch" in perm.all_keywords:
                    perm.damage = max(perm.damage, perm.toughness)

    def _check_mana_cost(self, player, mana_cost):
        """Returns error string if can't afford, else None."""
        pool = dict(player.mana_pool)
        generic = 0
        for sym, amt in mana_cost.items():
            if sym in ("W", "U", "B", "R", "G"):
                if pool.get(sym, 0) < amt:
                    return f"Mana insuficiente: precisa de {amt}{{{sym}}}."
                pool[sym] -= amt
            else:
                generic += int(amt)
        total_available = sum(pool.values())
        if total_available < generic:
            return f"Mana genérica insuficiente: precisa de {generic}."
        return None

    def _pay_mana(self, player, mana_cost):
        """Deduct mana cost from player's pool."""
        generic = 0
        for sym, amt in mana_cost.items():
            if sym in ("W", "U", "B", "R", "G"):
                player.mana_pool[sym] -= amt
            else:
                generic += int(amt)
        # Pay generic with whatever is available
        for color in ["C", "G", "R", "B", "U", "W"]:
            if generic <= 0:
                break
            available = player.mana_pool.get(color, 0)
            used = min(available, generic)
            player.mana_pool[color] -= used
            generic -= used

    def _validate_action(self, pid):
        if self.players[pid].lost:
            return "Você já perdeu o jogo."
        if self.players["p1"].won or self.players["p2"].won:
            return "O jogo já terminou."
        if pid != self.active_player and not self._can_respond(pid):
            return "Não é seu turno."
        return None

    def _can_respond(self, pid):
        """Can a non-active player respond? (instants / activated abilities)"""
        return self.phase not in (Phase.UNTAP, Phase.CLEANUP)

    def _log(self, msg):
        self.log.append(msg)
        if len(self.log) > 200:
            self.log = self.log[-200:]

    def _ok(self, data=None):
        return {"ok": True, **(data or {}), "state": self.to_dict()}

    def _err(self, msg):
        return {"ok": False, "error": msg, "state": self.to_dict()}

    # ══════════════════════════════════════
    #  SERIALIZE
    # ══════════════════════════════════════

    def to_dict(self, pov=None):
        """Serialize full game state."""
        return {
            "game_id":      self.game_id,
            "turn":         self.turn,
            "phase":        self.phase.value,
            "active_player": self.active_player,
            "priority":     self.priority,
            "waiting_action": self.waiting_action,
            "stack":        [s.to_dict() for s in self.stack],
            "battlefield":  [p.to_dict() for p in self.battlefield],
            "players":      {pid: p.to_dict(hide_hand=(pov and pov != pid))
                             for pid, p in self.players.items()},
            "log":          self.log[-30:],
            "combat_attackers": self.combat_attackers,
            "game_over":    self.players["p1"].lost or self.players["p2"].lost or
                            self.players["p1"].won  or self.players["p2"].won,
            "winner":       next((pid for pid, p in self.players.items() if p.won), None),
            "cards_db":     {k: {"id": v["id"], "name": v["name"], "type": v["type"],
                                  "mana_cost": v["mana_cost"], "cmc": v["cmc"],
                                  "power": v["power"], "toughness": v["toughness"],
                                  "keywords": v["keywords"], "oracle_text": v["oracle_text"],
                                  "color": v.get("color"), "subtypes": v.get("subtypes", [])}
                              for k, v in CARDS.items()},
        }
