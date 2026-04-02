from rest_framework import serializers
from .models import Card, Rule


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = [
            'scryfall_id', 'name', 'mana_cost', 'cmc',
            'type_line', 'oracle_text', 'rarity',
            'image_url_normal', 'set_code', 'release_date',
        ]


class CardListSerializer(serializers.Serializer):
    """Serializer para listagem agrupada por nome (resultado do GROUP BY)."""
    name = serializers.CharField()
    mana_cost = serializers.CharField(allow_null=True)
    type_line = serializers.CharField(allow_null=True)
    oracle_text = serializers.CharField(allow_null=True)
    rarity = serializers.CharField(allow_null=True)
    image_url_normal = serializers.CharField(allow_null=True)
    sets = serializers.ListField(child=serializers.DictField())
    latest_release = serializers.DateField(allow_null=True)


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = ['id', 'rule_number', 'rule_text', 'chapter_id']


class SetSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    released_at = serializers.CharField()
    icon_svg_uri = serializers.CharField()
    card_count = serializers.IntegerField()
