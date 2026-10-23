from django.contrib import admin

from .models import Categoria, Movimiento, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'stock', 'stock_minimo', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('codigo', 'nombre')

    def get_readonly_fields(self, request, obj=None):
        # Al editar, el stock solo cambia con movimientos
        return ('stock',) if obj else ()


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    """Solo lectura: los movimientos se registran desde la API para que
    el stock se actualice correctamente."""
    list_display = ('fecha', 'producto', 'tipo', 'cantidad', 'usuario')
    list_filter = ('tipo',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
