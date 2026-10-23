from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model
from django.db.models import F, ProtectedError, Q
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Categoria, Movimiento, Producto
from .serializers import (
    CategoriaSerializer, LoginSerializer, MovimientoSerializer,
    ProductoSerializer,
)

DIAS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']


class EliminarProtegidoMixin:
    """Responde 400 (y no 500) si se intenta borrar algo con registros asociados."""
    mensaje_protegido = 'No se puede eliminar: tiene registros asociados.'

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'detail': self.mensaje_protegido},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CategoriaViewSet(EliminarProtegidoMixin, viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    mensaje_protegido = 'No se puede eliminar: la categoría tiene productos asociados.'


class ProductoViewSet(EliminarProtegidoMixin, viewsets.ModelViewSet):
    queryset = Producto.objects.select_related('categoria')
    serializer_class = ProductoSerializer
    mensaje_protegido = 'No se puede eliminar: el producto tiene movimientos registrados.'

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        buscar = params.get('buscar')
        if buscar:
            qs = qs.filter(Q(nombre__icontains=buscar) | Q(codigo__icontains=buscar))

        categoria = params.get('categoria')
        if categoria:
            qs = qs.filter(categoria_id=categoria)

        estado = params.get('estado')
        if estado == 'agotado':
            qs = qs.filter(stock=0)
        elif estado == 'bajo':
            qs = qs.filter(stock__gt=0, stock__lte=F('stock_minimo'))
        elif estado == 'disponible':
            qs = qs.filter(stock__gt=F('stock_minimo'))
        return qs


class MovimientoViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Los movimientos solo se crean y consultan; no se editan ni se borran,
    para que el stock siempre coincida con el historial."""
    queryset = Movimiento.objects.select_related('producto', 'usuario')
    serializer_class = MovimientoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get('producto'):
            qs = qs.filter(producto_id=params['producto'])
        if params.get('tipo'):
            qs = qs.filter(tipo=params['tipo'].upper())
        return qs

    @action(detail=False, methods=['get'], url_path='resumen-semana')
    def resumen_semana(self, request):
        """Entradas y salidas de los últimos 7 días (para el gráfico del dashboard)."""
        hoy = timezone.localdate()
        inicio = hoy - timedelta(days=6)
        resumen = {
            inicio + timedelta(days=i): {'entradas': 0, 'salidas': 0}
            for i in range(7)
        }
        for mov in Movimiento.objects.filter(fecha__date__gte=inicio):
            dia = timezone.localtime(mov.fecha).date()
            if dia in resumen:
                clave = 'entradas' if mov.tipo == Movimiento.ENTRADA else 'salidas'
                resumen[dia][clave] += mov.cantidad

        return Response([
            {'fecha': dia.isoformat(), 'dia': DIAS[dia.weekday()], **valores}
            for dia, valores in resumen.items()
        ])


# ---------------------------------------------------------------------------
# Autenticación (token)
# ---------------------------------------------------------------------------
def datos_usuario(user):
    return {
        'id': user.pk,
        'usuario': user.get_username(),
        'nombre': user.get_full_name() or user.get_username(),
        'rol': 'Administrador' if (user.is_staff or user.is_superuser) else 'Operario',
    }


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.validated_data['usuario']
        password = serializer.validated_data['password']

        # El frontend permite escribir usuario o correo
        if '@' in usuario:
            encontrado = get_user_model().objects.filter(email__iexact=usuario).first()
            if encontrado:
                usuario = encontrado.get_username()

        user = authenticate(request, username=usuario, password=password)
        if user is None:
            return Response(
                {'detail': 'Usuario o contraseña incorrectos.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, **datos_usuario(user)})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(datos_usuario(request.user))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
