from datetime import timedelta
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import connection
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Categoria, Movimiento, Producto


class BaseAPITest(APITestCase):
    """Datos comunes para las pruebas."""

    def setUp(self):
        self.categoria = Categoria.objects.create(nombre='General')
        self.producto = Producto.objects.create(
            nombre='Cable', precio='1000', stock=10, stock_minimo=3,
            categoria=self.categoria,
        )

    def datos_producto(self, **extra):
        datos = {'nombre': 'Lapiz', 'precio': '1.50', 'stock': 10,
                 'stock_minimo': 2, 'categoria': self.categoria.id}
        datos.update(extra)
        return datos

    def mover(self, tipo, cantidad, producto=None):
        return self.client.post('/api/movimientos/', {
            'producto': (producto or self.producto).id,
            'tipo': tipo,
            'cantidad': cantidad,
        }, format='json')


class ProductoAPITest(BaseAPITest):
    def test_crear_producto(self):
        r = self.client.post('/api/productos/', self.datos_producto(), format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['categoria_nombre'], 'General')

    def test_codigo_se_genera_solo(self):
        r = self.client.post('/api/productos/', self.datos_producto(), format='json')
        self.assertEqual(r.data['codigo'], f"PRD-{r.data['id']:03d}")

    def test_codigo_repetido_es_rechazado(self):
        self.client.post('/api/productos/', self.datos_producto(codigo='ABC'), format='json')
        r = self.client.post('/api/productos/', self.datos_producto(codigo='ABC'), format='json')
        self.assertEqual(r.status_code, 400)

    def test_precio_negativo(self):
        r = self.client.post('/api/productos/', self.datos_producto(precio='-1'), format='json')
        self.assertEqual(r.status_code, 400)

    def test_categoria_inexistente(self):
        r = self.client.post('/api/productos/', self.datos_producto(categoria=9999), format='json')
        self.assertEqual(r.status_code, 400)

    def test_campo_obligatorio(self):
        r = self.client.post('/api/productos/', {'precio': '5'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_consultar_producto(self):
        r = self.client.get(f'/api/productos/{self.producto.id}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['nombre'], 'Cable')

    def test_listar_productos(self):
        r = self.client.get('/api/productos/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)

    def test_actualizar_producto(self):
        r = self.client.patch(f'/api/productos/{self.producto.id}/',
                              {'nombre': 'Cable 12'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.nombre, 'Cable 12')

    def test_no_se_cambia_el_stock_directamente(self):
        r = self.client.patch(f'/api/productos/{self.producto.id}/',
                              {'stock': 99}, format='json')
        self.assertEqual(r.status_code, 400)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_eliminar_producto(self):
        r = self.client.delete(f'/api/productos/{self.producto.id}/')
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Producto.objects.filter(pk=self.producto.id).exists())

    def test_no_elimina_producto_con_movimientos(self):
        self.mover('ENTRADA', 1)
        r = self.client.delete(f'/api/productos/{self.producto.id}/')
        self.assertEqual(r.status_code, 400)
        self.assertTrue(Producto.objects.filter(pk=self.producto.id).exists())

    def test_estados_de_stock(self):
        self.assertEqual(self.producto.estado_stock, 'disponible')
        self.producto.stock = 3
        self.assertEqual(self.producto.estado_stock, 'bajo')
        self.producto.stock = 0
        self.assertEqual(self.producto.estado_stock, 'agotado')

    def test_filtros_de_productos(self):
        Producto.objects.create(nombre='Breaker', precio='5', stock=0,
                                stock_minimo=5, categoria=self.categoria)
        self.assertEqual(len(self.client.get('/api/productos/?estado=agotado').data), 1)
        self.assertEqual(len(self.client.get('/api/productos/?estado=disponible').data), 1)
        self.assertEqual(len(self.client.get('/api/productos/?buscar=cab').data), 1)
        self.assertEqual(
            len(self.client.get(f'/api/productos/?categoria={self.categoria.id}').data), 2)


class CategoriaAPITest(BaseAPITest):
    def test_listar_categorias(self):
        r = self.client.get('/api/categorias/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)

    def test_crear_categoria(self):
        r = self.client.post('/api/categorias/', {'nombre': 'Cables'}, format='json')
        self.assertEqual(r.status_code, 201)

    def test_no_elimina_categoria_con_productos(self):
        r = self.client.delete(f'/api/categorias/{self.categoria.id}/')
        self.assertEqual(r.status_code, 400)
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.id).exists())


class MovimientoAPITest(BaseAPITest):
    def test_entrada_aumenta_el_stock(self):
        r = self.mover('ENTRADA', 5)
        self.assertEqual(r.status_code, 201)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 15)

    def test_salida_disminuye_el_stock(self):
        r = self.mover('SALIDA', 4)
        self.assertEqual(r.status_code, 201)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 6)

    def test_salida_con_stock_insuficiente(self):
        r = self.mover('SALIDA', 11)
        self.assertEqual(r.status_code, 400)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)
        self.assertEqual(Movimiento.objects.count(), 0)

    def test_salida_por_todo_el_stock(self):
        self.assertEqual(self.mover('SALIDA', 10).status_code, 201)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 0)

    def test_cantidad_cero_o_negativa(self):
        self.assertEqual(self.mover('ENTRADA', 0).status_code, 400)
        self.assertEqual(self.mover('ENTRADA', -3).status_code, 400)

    def test_tipo_invalido(self):
        self.assertEqual(self.mover('PRESTAMO', 1).status_code, 400)

    def test_producto_inactivo(self):
        self.producto.activo = False
        self.producto.save()
        self.assertEqual(self.mover('ENTRADA', 1).status_code, 400)

    def test_consultar_movimientos(self):
        self.mover('ENTRADA', 2)
        self.mover('SALIDA', 1)
        r = self.client.get('/api/movimientos/')
        self.assertEqual(len(r.data), 2)
        r = self.client.get('/api/movimientos/?tipo=entrada')
        self.assertEqual(len(r.data), 1)
        r = self.client.get(f'/api/movimientos/?producto={self.producto.id}')
        self.assertEqual(len(r.data), 2)

    def test_movimientos_no_se_editan_ni_se_borran(self):
        mov_id = self.mover('ENTRADA', 2).data['id']
        self.assertEqual(self.client.patch(f'/api/movimientos/{mov_id}/', {'cantidad': 9},
                                           format='json').status_code, 405)
        self.assertEqual(self.client.delete(f'/api/movimientos/{mov_id}/').status_code, 405)

    def test_resumen_de_la_semana(self):
        self.mover('ENTRADA', 5)
        self.mover('SALIDA', 2)
        # Un movimiento de hace 30 dias no debe contarse
        viejo = Movimiento.objects.create(producto=self.producto, tipo='ENTRADA', cantidad=50)
        Movimiento.objects.filter(pk=viejo.pk).update(fecha=timezone.now() - timedelta(days=30))

        r = self.client.get('/api/movimientos/resumen-semana/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 7)
        self.assertEqual(sum(d['entradas'] for d in r.data), 5)
        self.assertEqual(sum(d['salidas'] for d in r.data), 2)


class AutenticacionTest(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='ana', email='ana@correo.com', password='clave12345',
            first_name='Ana', is_staff=True,
        )

    def login(self, usuario, password):
        return self.client.post('/api/auth/login/',
                                {'usuario': usuario, 'password': password}, format='json')

    def test_login_correcto(self):
        r = self.login('ana', 'clave12345')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data['token'])
        self.assertEqual(r.data['nombre'], 'Ana')
        self.assertEqual(r.data['rol'], 'Administrador')

    def test_login_con_correo(self):
        self.assertEqual(self.login('ana@correo.com', 'clave12345').status_code, 200)

    def test_login_incorrecto(self):
        self.assertEqual(self.login('ana', 'mala').status_code, 401)

    def test_login_sin_datos(self):
        self.assertEqual(self.client.post('/api/auth/login/', {}, format='json').status_code, 400)

    def test_me_con_y_sin_token(self):
        self.assertIn(self.client.get('/api/auth/me/').status_code, (401, 403))
        token = self.login('ana', 'clave12345').data['token']
        r = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['usuario'], 'ana')

    def test_logout_invalida_el_token(self):
        token = self.login('ana', 'clave12345').data['token']
        cabecera = {'HTTP_AUTHORIZATION': f'Token {token}'}
        self.assertEqual(self.client.post('/api/auth/logout/', **cabecera).status_code, 204)
        self.assertIn(self.client.get('/api/auth/me/', **cabecera).status_code, (401, 403))

    def test_el_movimiento_guarda_el_usuario(self):
        cat = Categoria.objects.create(nombre='X')
        prod = Producto.objects.create(nombre='P', precio='1', stock=5, categoria=cat)
        token = self.login('ana', 'clave12345').data['token']
        r = self.client.post('/api/movimientos/',
                             {'producto': prod.id, 'tipo': 'ENTRADA', 'cantidad': 1},
                             format='json', HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(r.data['usuario_nombre'], 'ana')


class BaseDeDatosTest(APITestCase):
    def test_hay_conexion(self):
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            self.assertEqual(cursor.fetchone()[0], 1)

    @skipUnless(connection.vendor == 'mysql',
                'Solo se ejecuta cuando DB_ENGINE=mysql en el .env')
    def test_conexion_mysql(self):
        self.assertEqual(connection.vendor, 'mysql')
