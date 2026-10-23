from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoriaViewSet, LoginView, LogoutView, MeView, MovimientoViewSet,
    ProductoViewSet,
)

router = DefaultRouter()
router.register('categorias', CategoriaViewSet)
router.register('productos', ProductoViewSet)
router.register('movimientos', MovimientoViewSet)

urlpatterns = [
    path('auth/login/', LoginView.as_view()),
    path('auth/me/', MeView.as_view()),
    path('auth/logout/', LogoutView.as_view()),
    path('', include(router.urls)),
]
