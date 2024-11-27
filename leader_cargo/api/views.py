from rest_framework import generics

from analytics.models import CargoArticle

from .serializers import CargoArticleSerializer


class WomenAPIView(generics.ListAPIView):
    queryset = CargoArticle.objects.all()
    serializer_class = CargoArticleSerializer
