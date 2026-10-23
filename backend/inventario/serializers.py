from django.db import transaction
from rest_framework import serializers

from .models import Categoria, Movimiento, Producto


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class ProductoSerializer(serializers.ModelSerializer):
    # Campos de solo lectura que el frontend necesita para mostrar la tabla
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    estado_stock = serializers.CharField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id', 'codigo', 'nombre', 'descripcion', 'precio', 'stock',
            'stock_minimo', 'activo', 'categoria', 'categoria_nombre',
            'estado_stock', 'creado',
        ]

    def validate_precio(self, value):
        if value < 0:
            raise serializers.ValidationError('El precio no puede ser negativo.')
        return value

    def validate_stock(self, value):
        # El stock inicial se define al crear; después solo cambia con movimientos
        if self.instance is not None and value != self.instance.stock:
            raise serializers.ValidationError(
                'El stock solo cambia registrando movimientos de inventario.'
            )
        return value


class MovimientoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Movimiento
        fields = [
            'id', 'producto', 'producto_nombre', 'tipo', 'cantidad',
            'observaciones', 'usuario', 'usuario_nombre', 'fecha',
        ]
        read_only_fields = ['usuario', 'fecha']
        extra_kwargs = {'cantidad': {'min_value': 1}}

    def get_usuario_nombre(self, obj):
        return obj.usuario.get_username() if obj.usuario else None

    def validate_producto(self, producto):
        if not producto.activo:
            raise serializers.ValidationError('El producto está inactivo.')
        return producto

    def create(self, validated_data):
        """Registra el movimiento y actualiza el stock en una sola operación."""
        request = self.context.get('request')
        usuario = request.user if request and request.user.is_authenticated else None

        with transaction.atomic():
            # select_for_update bloquea la fila para evitar salidas simultáneas
            producto = Producto.objects.select_for_update().get(
                pk=validated_data['producto'].pk
            )
            cantidad = validated_data['cantidad']

            if validated_data['tipo'] == Movimiento.SALIDA:
                if cantidad > producto.stock:
                    raise serializers.ValidationError({
                        'cantidad': f'Stock insuficiente. Disponible: {producto.stock}.'
                    })
                producto.stock -= cantidad
            else:
                producto.stock += cantidad

            producto.save(update_fields=['stock'])
            validated_data['usuario'] = usuario
            return super().create(validated_data)


class LoginSerializer(serializers.Serializer):
    usuario = serializers.CharField()
    password = serializers.CharField()
