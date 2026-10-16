from rest_framework.test import APITestCase
from .models import Categoria


class ProductoAPITest(APITestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre='General')

    def test_crear_producto(self):
        datos = {'nombre': 'Lapiz', 'precio': '1.50', 'stock': 10,
                 'categoria': self.categoria.id}
        r = self.client.post('/api/productos/', datos, format='json')
        self.assertEqual(r.status_code, 201)

    def test_precio_negativo(self):
        datos = {'nombre': 'Lapiz', 'precio': '-1', 'stock': 10,
                 'categoria': self.categoria.id}
        r = self.client.post('/api/productos/', datos, format='json')
        self.assertEqual(r.status_code, 400)