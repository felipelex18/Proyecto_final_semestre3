from django.db import migrations


def asignar_codigos(apps, schema_editor):
    """Da un código (PRD-001, PRD-002...) a los productos creados antes de
    que existiera el campo."""
    Producto = apps.get_model('inventario', 'Producto')
    for producto in Producto.objects.filter(codigo__isnull=True):
        producto.codigo = f'PRD-{producto.pk:03d}'
        producto.save(update_fields=['codigo'])


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0002_movimientos_y_campos_producto'),
    ]

    operations = [
        migrations.RunPython(asignar_codigos, migrations.RunPython.noop),
    ]
