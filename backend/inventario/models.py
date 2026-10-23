from django.conf import settings
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    # Si no se envía un código, se genera solo al guardar (PRD-001, PRD-002...)
    codigo = models.CharField(max_length=30, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name='productos'
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.nombre

    @property
    def estado_stock(self):
        """Misma regla que usa el frontend: agotado, bajo o disponible."""
        if self.stock == 0:
            return 'agotado'
        if self.stock <= self.stock_minimo:
            return 'bajo'
        return 'disponible'

    def save(self, *args, **kwargs):
        # Un texto vacío se guarda como NULL para no chocar con la regla de único
        if not self.codigo:
            self.codigo = None
        super().save(*args, **kwargs)
        if not self.codigo:
            self.codigo = f'PRD-{self.pk:03d}'
            super().save(update_fields=['codigo'])


class Movimiento(models.Model):
    ENTRADA = 'ENTRADA'
    SALIDA = 'SALIDA'
    TIPOS = [(ENTRADA, 'Entrada'), (SALIDA, 'Salida')]

    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name='movimientos'
    )
    tipo = models.CharField(max_length=7, choices=TIPOS)
    cantidad = models.PositiveIntegerField()
    observaciones = models.TextField(blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='movimientos'
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f'{self.tipo} de {self.cantidad} x {self.producto}'
