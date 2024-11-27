from rest_framework import serializers

from analytics.models import CargoArticle

class CargoArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoArticle
        fields = ('article', 'responsible_manager', 'carrier', 'name_goods')
