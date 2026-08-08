@echo off
call .venv\Scripts\activate.bat
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings'); django.setup(); from ventasweb.models import Articulo; arts = Articulo.objects.all()[:20]; print(f'Total articulos: {Articulo.objects.count()}'); [print(f'{a.id} - {a.nombre} - Activo:{a.activo}') for a in arts]"
pause
