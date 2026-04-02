"""
game_views.py — API REST para o motor do jogo
"""
import uuid
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .game_engine.game import GameEngine
from .game_engine.cards_db import DECKS, CARDS

# In-memory game store (replace with Redis/DB for production)
GAMES = {}


@api_view(['GET'])
def list_decks(request):
    """GET /api/game/decks/ — lista decks disponíveis"""
    return Response({
        "decks": [
            {"id": k, "name": v["name"], "colors": v["colors"],
             "card_count": len(v["cards"])}
            for k, v in DECKS.items()
        ]
    })


@api_view(['POST'])
def create_game(request):
    """POST /api/game/create/ — cria nova partida"""
    data    = request.data
    game_id = str(uuid.uuid4())[:8]

    p1_deck = data.get("p1_deck", "green_stompy")
    p2_deck = data.get("p2_deck", "red_aggro")
    p1_name = data.get("p1_name", "Jogador")
    p2_name = data.get("p2_name", "Oponente IA")

    game = GameEngine(game_id, p1_name, p1_deck, p2_name, p2_deck)
    GAMES[game_id] = game

    return Response({"game_id": game_id, "state": game.to_dict(pov="p1")})


@api_view(['GET'])
def get_game(request, game_id):
    """GET /api/game/<id>/ — estado atual"""
    game = GAMES.get(game_id)
    if not game:
        return Response({"error": "Jogo não encontrado."}, status=404)
    return Response(game.to_dict(pov="p1"))


@api_view(['POST'])
def game_action(request, game_id):
    """POST /api/game/<id>/action/ — executa uma ação"""
    game = GAMES.get(game_id)
    if not game:
        return Response({"error": "Jogo não encontrado."}, status=404)

    action  = request.data.get("action")
    pid     = request.data.get("pid", "p1")
    payload = request.data.get("payload", {})

    result = {}

    if action == "play_land":
        result = game.play_land(pid, payload.get("card_id"))

    elif action == "cast_spell":
        result = game.cast_spell(pid, payload.get("card_id"), payload.get("targets", []))

    elif action == "activate_ability":
        result = game.activate_ability(pid, payload.get("perm_uid"),
                                       payload.get("ability_index", 0),
                                       payload.get("targets", []))

    elif action == "declare_attackers":
        result = game.declare_attackers(pid, payload.get("attacker_uids", []))
        # After declaring, AI responds
        _maybe_ai_respond(game)

    elif action == "declare_blockers":
        result = game.declare_blockers(pid, payload.get("block_assignments", {}))

    elif action == "pass_priority":
        result = game.pass_priority(pid)
        # AI takes its turn if needed
        _maybe_ai_turn(game)

    elif action == "end_phase":
        result = game.end_phase(pid)
        _maybe_ai_turn(game)

    elif action == "resolve_stack":
        result = game.resolve_stack(pid)

    else:
        result = {"ok": False, "error": f"Ação desconhecida: {action}"}

    # Always return full state
    result["state"] = game.to_dict(pov="p1")
    return Response(result)


def _maybe_ai_turn(game):
    """Run AI turn if it's p2's turn and in main phase."""
    if game.active_player != "p2":
        return
    if game.players["p2"].lost or game.players["p1"].won:
        return

    from .game_engine.game import Phase
    if game.phase in (Phase.MAIN1, Phase.MAIN2):
        game._ai_take_turn()
        # AI passes to combat or end
        if game.phase == Phase.MAIN1:
            game._advance_to(Phase.COMBAT_BEGIN)
            game._advance_to(Phase.COMBAT_ATTACKERS)
            # AI attacks
            attackers = []
            for perm in game.battlefield:
                if perm.controller == "p2" and perm.can_attack():
                    attackers.append(perm.uid)
            game.declare_attackers("p2", attackers)


def _maybe_ai_respond(game):
    """AI responds to player actions if needed."""
    pass
