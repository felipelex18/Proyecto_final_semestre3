from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoriaViewSet, ProductoViewSet

router = DefaultRouter()
router.register('categorías', CategoriaViewSet)
router.register('productos', ProductoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

