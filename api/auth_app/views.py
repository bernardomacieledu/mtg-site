"""
auth_views.py — Autenticação JWT + CRUD de decks e coleções por usuário
"""
import jwt
import datetime
from functools import wraps

from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import User, UserDeck, UserCollection

JWT_SECRET  = getattr(settings, 'JWT_SECRET', 'mtg-nexus-jwt-secret-change-in-production')
JWT_ALGO    = 'HS256'
JWT_EXPIRY  = 7  # days


# ── JWT helpers ───────────────────────────────────────────────────────────────

def make_token(user):
    payload = {
        'uid':      user.id,
        'username': user.username,
        'exp':      datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXPIRY),
        'iat':      datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def admin_required(f):
    """
    Exige token válido E privilégio de administrador.

    Envolve o jwt_required para não duplicar a validação do token; devolve 403
    (e não 404) quando o usuário está autenticado mas não é administrador, para
    a interface poder distinguir "não logado" de "sem permissão".
    """
    @wraps(f)
    @jwt_required
    def wrapper(request, *args, **kwargs):
        usuario = request.user_obj
        if not (usuario.is_staff or usuario.is_superuser):
            return Response({'error': 'Acesso restrito a administradores.'}, status=403)
        return f(request, *args, **kwargs)
    return wrapper


def jwt_required(f):
    """Decorator: extrai e valida o JWT do header Authorization."""
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return Response({'error': 'Token não fornecido.'}, status=401)
        payload = decode_token(auth[7:])
        if not payload:
            return Response({'error': 'Token inválido ou expirado.'}, status=401)
        try:
            request.user_obj = User.objects.get(id=payload['uid'])
        except User.DoesNotExist:
            return Response({'error': 'Usuário não encontrado.'}, status=401)
        return f(request, *args, **kwargs)
    return wrapper


# ── Auth endpoints ────────────────────────────────────────────────────────────

@api_view(['POST'])
def register(request):
    """POST /api/auth/register/ — cria conta."""
    username = request.data.get('username', '').strip()
    email    = request.data.get('email', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response({'error': 'Username e senha são obrigatórios.'}, status=400)
    if len(password) < 6:
        return Response({'error': 'Senha deve ter no mínimo 6 caracteres.'}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username já está em uso.'}, status=400)
    if email and User.objects.filter(email=email).exists():
        return Response({'error': 'Email já cadastrado.'}, status=400)

    user = User.objects.create(
        username=username,
        email=email or f'{username}@local',
        password=make_password(password),
    )

    token = make_token(user)
    return Response({
        'token':    token,
        'username': user.username,
        'uid':      user.id,
        'is_admin': user.is_staff or user.is_superuser,
    }, status=201)


@api_view(['POST'])
def login(request):
    """POST /api/auth/login/ — autentica e retorna JWT."""
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response({'error': 'Credenciais inválidas.'}, status=400)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': 'Usuário ou senha incorretos.'}, status=401)

    if not check_password(password, user.password):
        return Response({'error': 'Usuário ou senha incorretos.'}, status=401)

    token = make_token(user)
    return Response({
        'token':    token,
        'username': user.username,
        'uid':      user.id,
        'is_admin': user.is_staff or user.is_superuser,
    })


@api_view(['GET'])
@jwt_required
def me(request):
    """GET /api/auth/me/ — retorna dados do usuário logado."""
    user = request.user_obj
    return Response({
        'uid':      user.id,
        'username': user.username,
        'email':    user.email,
        'is_admin':          user.is_staff or user.is_superuser,
        'decks_count':       user.decks.count(),
        'collections_count': user.collections.count(),
    })


# ── Decks ─────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@jwt_required
def list_decks(request):
    """GET /api/auth/decks/ — lista decks do usuário."""
    decks = request.user_obj.decks.all()
    return Response([{
        'id':         d.id,
        'name':       d.name,
        'colors':     d.colors,
        'total_cards': d.total_cards,
        'avg_cmc':    d.avg_cmc,
        'commander':  d.commander_json,
        'not_found':  d.not_found,
        'active_imgs': d.active_imgs,
        'updated_at': d.updated_at.isoformat(),
    } for d in decks])


@api_view(['POST'])
@jwt_required
def create_deck(request):
    """POST /api/auth/decks/ — cria ou atualiza deck."""
    data = request.data
    deck_id = data.get('id')

    fields = {
        'name':            data.get('name', 'Deck sem nome'),
        'raw_text':        data.get('raw_text', ''),
        'cards_json':      data.get('cards', []),
        'categorized_json': data.get('categorized', {}),
        'commander_json':  data.get('commander'),
        'legendaries_json': data.get('legendaries', []),
        'colors':          data.get('colors', []),
        'total_cards':     data.get('total_cards', 0),
        'avg_cmc':         data.get('avg_cmc', 0),
        'not_found':       data.get('not_found', []),
        'active_imgs':     data.get('active_imgs', {}),
    }

    if deck_id:
        try:
            deck = UserDeck.objects.get(id=deck_id, user=request.user_obj)
            for k, v in fields.items():
                setattr(deck, k, v)
            deck.save()
        except UserDeck.DoesNotExist:
            return Response({'error': 'Deck não encontrado.'}, status=404)
    else:
        deck = UserDeck.objects.create(user=request.user_obj, **fields)

    return Response({'id': deck.id, 'name': deck.name, 'updated_at': deck.updated_at.isoformat()})


@api_view(['GET'])
@jwt_required
def get_deck(request, deck_id):
    """GET /api/auth/decks/<id>/ — retorna deck completo."""
    try:
        d = UserDeck.objects.get(id=deck_id, user=request.user_obj)
    except UserDeck.DoesNotExist:
        return Response({'error': 'Deck não encontrado.'}, status=404)

    return Response({
        'id':          d.id,
        'name':        d.name,
        'raw_text':    d.raw_text,
        'cards':       d.cards_json,
        'categorized': d.categorized_json,
        'commander':   d.commander_json,
        'legendaries': d.legendaries_json,
        'colors':      d.colors,
        'total_cards': d.total_cards,
        'avg_cmc':     d.avg_cmc,
        'not_found':   d.not_found,
        'active_imgs': d.active_imgs,
        'updated_at':  d.updated_at.isoformat(),
    })


@api_view(['DELETE'])
@jwt_required
def delete_deck(request, deck_id):
    """DELETE /api/auth/decks/<id>/"""
    try:
        UserDeck.objects.get(id=deck_id, user=request.user_obj).delete()
    except UserDeck.DoesNotExist:
        return Response({'error': 'Deck não encontrado.'}, status=404)
    return Response({'deleted': True})


@api_view(['PATCH'])
@jwt_required
def update_deck_imgs(request, deck_id):
    """PATCH /api/auth/decks/<id>/imgs/ — atualiza imagens ativas."""
    try:
        deck = UserDeck.objects.get(id=deck_id, user=request.user_obj)
        deck.active_imgs = {**deck.active_imgs, **request.data.get('active_imgs', {})}
        deck.save(update_fields=['active_imgs'])
    except UserDeck.DoesNotExist:
        return Response({'error': 'Deck não encontrado.'}, status=404)
    return Response({'active_imgs': deck.active_imgs})


# ── Collections (múltiplas por usuário) ──────────────────────────────────────

def _collection_summary(col):
    stats = col.stats_json or {}
    return {
        'id':           col.id,
        'name':         col.name,
        'total_copies': stats.get('total_copies', 0),
        'total_unique': stats.get('total_unique', len(col.cards_json or [])),
        'total_sets':   stats.get('total_sets', 0),
        'updated_at':   col.updated_at.isoformat(),
    }


def _collection_payload(col):
    return {
        'exists':      True,
        'id':          col.id,
        'name':        col.name,
        'cards':       col.cards_json,
        'by_set':      col.by_set_json,
        'by_rarity':   col.by_rarity_json,
        'by_category': col.by_category_json,
        'stats':       col.stats_json,
        'active_imgs': col.active_imgs,
        'updated_at':  col.updated_at.isoformat(),
    }


def _fields_from_request(data):
    return {
        'name':             data.get('name', 'Minha Coleção'),
        'cards_json':       data.get('cards', []),
        'by_set_json':      data.get('by_set', []),
        'by_rarity_json':   data.get('by_rarity', {}),
        'by_category_json': data.get('by_category', {}),
        'stats_json':       data.get('stats', {}),
        'active_imgs':      data.get('active_imgs', {}),
    }


@api_view(['GET'])
@jwt_required
def list_collections(request):
    """GET /api/auth/collections/ — lista todas as coleções do usuário."""
    return Response([_collection_summary(c) for c in request.user_obj.collections.all()])


@api_view(['GET'])
@jwt_required
def get_collection_by_id(request, collection_id):
    """GET /api/auth/collections/<id>/ — retorna uma coleção completa."""
    try:
        col = UserCollection.objects.get(id=collection_id, user=request.user_obj)
    except UserCollection.DoesNotExist:
        return Response({'error': 'Coleção não encontrada.'}, status=404)
    return Response(_collection_payload(col))


@api_view(['POST'])
@jwt_required
def save_collection_multi(request):
    """
    POST /api/auth/collections/save/ — cria ou atualiza.
    Com "id" no corpo, atualiza a coleção correspondente; sem "id", cria uma nova.
    """
    data = request.data
    fields = _fields_from_request(data)
    collection_id = data.get('id')

    if collection_id:
        try:
            col = UserCollection.objects.get(id=collection_id, user=request.user_obj)
        except UserCollection.DoesNotExist:
            return Response({'error': 'Coleção não encontrada.'}, status=404)
        for key, value in fields.items():
            setattr(col, key, value)
        col.save()
    else:
        col = UserCollection.objects.create(user=request.user_obj, **fields)

    return Response({'id': col.id, 'name': col.name, 'updated_at': col.updated_at.isoformat()},
                    status=200 if collection_id else 201)


@api_view(['DELETE'])
@jwt_required
def delete_collection(request, collection_id):
    """DELETE /api/auth/collections/<id>/delete/"""
    deleted, _ = UserCollection.objects.filter(id=collection_id, user=request.user_obj).delete()
    if not deleted:
        return Response({'error': 'Coleção não encontrada.'}, status=404)
    return Response({'deleted': True})


@api_view(['PATCH'])
@jwt_required
def rename_collection(request, collection_id):
    """PATCH /api/auth/collections/<id>/rename/"""
    name = (request.data.get('name') or '').strip()
    if not name:
        return Response({'error': 'Nome obrigatório.'}, status=400)
    try:
        col = UserCollection.objects.get(id=collection_id, user=request.user_obj)
    except UserCollection.DoesNotExist:
        return Response({'error': 'Coleção não encontrada.'}, status=404)
    col.name = name
    col.save(update_fields=['name', 'updated_at'])
    return Response({'id': col.id, 'name': col.name})


# ── Compatibilidade: endpoints antigos de coleção única ──────────────────────

@api_view(['GET'])
@jwt_required
def get_collection(request):
    """GET /api/auth/collection/ — primeira coleção do usuário."""
    col = request.user_obj.collections.first()
    if not col:
        return Response({'exists': False, 'cards': [], 'stats': None})
    return Response(_collection_payload(col))


@api_view(['POST'])
@jwt_required
def save_collection(request):
    """POST /api/auth/collection/ — salva/atualiza a primeira coleção."""
    col = request.user_obj.collections.first()
    fields = _fields_from_request(request.data)

    if col:
        for key, value in fields.items():
            setattr(col, key, value)
        col.save()
    else:
        col = UserCollection.objects.create(user=request.user_obj, **fields)

    return Response({'id': col.id, 'updated_at': col.updated_at.isoformat()})


@api_view(['PATCH'])
@jwt_required
def update_collection_imgs(request, collection_id=None):
    """PATCH /api/auth/collection/imgs/ — atualiza imagens ativas."""
    if collection_id:
        col = UserCollection.objects.filter(id=collection_id, user=request.user_obj).first()
    else:
        col = request.user_obj.collections.first()
    if not col:
        return Response({'error': 'Coleção não encontrada.'}, status=404)
    col.active_imgs = {**(col.active_imgs or {}), **request.data.get('active_imgs', {})}
    col.save(update_fields=['active_imgs', 'updated_at'])
    return Response({'active_imgs': col.active_imgs})
