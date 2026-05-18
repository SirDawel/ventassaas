"""
Vistas para importación masiva de usuarios mediante archivos CSV
"""
import csv
import io
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import CustomUser, GrupoFamiliar
from .forms import ImportarUsuariosCSVForm


@login_required
def importar_usuarios_csv_vista(request):
    """Vista para mostrar el formulario de importación y procesar el archivo CSV"""
    if request.user.rol not in ['Administrador', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    if request.method == 'POST':
        form = ImportarUsuariosCSVForm(request.POST, request.FILES)
        if form.is_valid():
            archivo_csv = request.FILES['archivo_csv']
            resultado = procesar_csv_usuarios(archivo_csv, request.user)
            
            # Mostrar resultados
            total_procesados = resultado['exitosos'] + len(resultado['errores'])
            
            if resultado['exitosos'] > 0:
                if resultado['exitosos'] == 1:
                    usuario_info = resultado['usuarios_creados'][0]
                    messages.success(request, 
                        f'✅ Se ha importado exitosamente 1 usuario: {usuario_info["nombre"]} ({usuario_info["rol"]})')
                else:
                    messages.success(request, 
                        f'✅ Se han importado exitosamente {resultado["exitosos"]} usuarios:')
                    
                    # Mostrar lista de usuarios creados (máximo 10)
                    for usuario_info in resultado['usuarios_creados'][:10]:
                        messages.success(request, 
                            f'   ✓ {usuario_info["nombre"]} - {usuario_info["rol"]} ({usuario_info["email"]})')
                    
                    if len(resultado['usuarios_creados']) > 10:
                        messages.success(request, 
                            f'   ... y {len(resultado["usuarios_creados"]) - 10} usuario(s) más.')
            
            if resultado['errores']:
                messages.warning(request, 
                    f'⚠️ Se encontraron {len(resultado["errores"])} error(es) durante la importación:')
                
                for error in resultado['errores'][:10]:  # Mostrar solo los primeros 10 errores
                    messages.warning(request, f'   • {error}')
                
                if len(resultado['errores']) > 10:
                    messages.info(request, 
                        f'   ... y {len(resultado["errores"]) - 10} error(es) más.')
            
            # Mensaje de resumen final
            if resultado['exitosos'] > 0 or resultado['errores']:
                messages.info(request, 
                    f'📊 Resumen: {resultado["exitosos"]} importados / {len(resultado["errores"])} con errores / {total_procesados} procesados en total')
            else:
                messages.warning(request, 'No se procesaron usuarios. Verifica el formato del archivo CSV.')
            
            return redirect('importar_usuarios_csv')
    else:
        form = ImportarUsuariosCSVForm()
    
    context = {
        'form': form,
        'titulo': 'Importar Usuarios desde CSV',
    }
    return render(request, 'users/importar_csv.html', context)


def procesar_csv_usuarios(archivo_csv, usuario_creador):
    """
    Procesa el archivo CSV y crea los usuarios
    Retorna un diccionario con estadísticas del proceso
    """
    resultado = {
        'exitosos': 0,
        'errores': [],
        'usuarios_creados': []  # Lista de usuarios creados con sus datos
    }
    
    try:
        # Leer el archivo CSV con múltiples codificaciones
        contenido_bytes = archivo_csv.read()
        archivo_decoded = None
        
        # Intentar varias codificaciones comunes
        codificaciones = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in codificaciones:
            try:
                archivo_decoded = contenido_bytes.decode(encoding)
                break  # Si funciona, salir del loop
            except (UnicodeDecodeError, AttributeError):
                continue
        
        if archivo_decoded is None:
            resultado['errores'].append(
                'No se pudo decodificar el archivo. Asegúrate de que sea un archivo CSV válido.'
            )
            return resultado
        
        csv_data = csv.DictReader(io.StringIO(archivo_decoded))
        
        # Validar que tenga las columnas requeridas
        columnas_requeridas = ['email', 'first_name', 'last_name', 'rol']
        columnas_archivo = csv_data.fieldnames
        
        for columna in columnas_requeridas:
            if columna not in columnas_archivo:
                resultado['errores'].append(
                    f'Falta la columna requerida: {columna}'
                )
                return resultado
        
        # Procesar cada fila
        for linea_num, fila in enumerate(csv_data, start=2):  # start=2 porque línea 1 son headers
            try:
                with transaction.atomic():
                    # Validar campos obligatorios
                    email = fila.get('email', '').strip()
                    first_name = fila.get('first_name', '').strip()
                    last_name = fila.get('last_name', '').strip()
                    rol = fila.get('rol', '').strip()
                    
                    if not all([email, first_name, last_name, rol]):
                        resultado['errores'].append(
                            f'Línea {linea_num}: Faltan campos obligatorios (email, nombre, apellido, rol)'
                        )
                        continue
                    
                    # Validar que el rol sea válido
                    roles_validos = ['Estudiante', 'Profesor', 'Director', 'Secretaria', 
                                   'Administrador', 'Coordinador', 'Bibliotecario', 
                                   'Psicologo', 'Otro']
                    if rol not in roles_validos:
                        resultado['errores'].append(
                            f'Línea {linea_num}: Rol inválido "{rol}". Roles válidos: {", ".join(roles_validos)}'
                        )
                        continue
                    
                    # Verificar si el usuario ya existe
                    if CustomUser.objects.filter(email=email).exists():
                        resultado['errores'].append(
                            f'Línea {linea_num}: El email {email} ya existe'
                        )
                        continue
                    
                    # Verificar cédula si se proporciona
                    cedula = fila.get('cedula', '').strip()
                    if cedula and CustomUser.objects.filter(cedula=cedula).exists():
                        resultado['errores'].append(
                            f'Línea {linea_num}: La cédula {cedula} ya existe'
                        )
                        continue
                    
                    # Crear el usuario
                    usuario = CustomUser(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        rol=rol,
                        is_active=True
                    )
                    
                    # Campos opcionales
                    if cedula:
                        usuario.cedula = cedula
                    
                    fecha_nacimiento = fila.get('fecha_nacimiento', '').strip()
                    if fecha_nacimiento:
                        try:
                            # Intentar varios formatos de fecha
                            for formato in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                                try:
                                    usuario.fecha_nacimiento = datetime.strptime(fecha_nacimiento, formato).date()
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            resultado['errores'].append(
                                f'Línea {linea_num}: Formato de fecha inválido "{fecha_nacimiento}". Use YYYY-MM-DD o DD/MM/YYYY'
                            )
                            continue
                    
                    genero = fila.get('genero', '').strip()
                    if genero and genero in ['M', 'F', 'Otro']:
                        usuario.genero = genero
                    
                    direccion = fila.get('direccion', '').strip()
                    if direccion:
                        usuario.direccion = direccion
                    
                    telefono = fila.get('telefono', '').strip()
                    if telefono:
                        usuario.telefono = telefono
                    
                    # Campos específicos por rol
                    if rol == 'Estudiante':
                        grado = fila.get('grado', '').strip()
                        if grado:
                            usuario.grado = grado
                        
                        seccion = fila.get('seccion', '').strip()
                        if seccion:
                            usuario.seccion = seccion
                    
                    elif rol in ['Profesor', 'Coordinador']:
                        especialidad = fila.get('especialidad', '').strip()
                        if especialidad:
                            usuario.especialidad = especialidad
                        
                        departamento = fila.get('departamento', '').strip()
                        if departamento:
                            usuario.departamento = departamento
                    
                    elif rol in ['Director', 'Secretaria', 'Administrador']:
                        cargo = fila.get('cargo', '').strip()
                        if cargo:
                            usuario.cargo = cargo
                        
                        departamento = fila.get('departamento', '').strip()
                        if departamento:
                            usuario.departamento = departamento
                    
                    # Establecer contraseña
                    password = fila.get('password', '').strip()
                    if password:
                        usuario.set_password(password)
                    else:
                        # Contraseña por defecto: cedula si existe, sino email sin @dominio
                        password_default = cedula if cedula else email.split('@')[0]
                        usuario.set_password(password_default)
                    
                    # Guardar usuario
                    usuario.save()
                    resultado['exitosos'] += 1
                    resultado['usuarios_creados'].append({
                        'nombre': f'{first_name} {last_name}',
                        'email': email,
                        'rol': rol
                    })
                    
            except Exception as e:
                resultado['errores'].append(
                    f'Línea {linea_num}: Error al procesar - {str(e)}'
                )
                continue
    
    except Exception as e:
        resultado['errores'].append(f'Error al leer el archivo CSV: {str(e)}')
    
    return resultado


@login_required
def descargar_plantilla_csv(request):
    """Descarga un archivo CSV de plantilla para importar usuarios"""
    if request.user.rol not in ['Administrador', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Crear el archivo CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="plantilla_usuarios.csv"'
    
    # Agregar BOM para que Excel lo abra correctamente con UTF-8
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    # Encabezados
    writer.writerow([
        'email',
        'first_name',
        'last_name',
        'rol',
        'cedula',
        'fecha_nacimiento',
        'genero',
        'telefono',
        'direccion',
        'grado',
        'seccion',
        'especialidad',
        'departamento',
        'cargo',
        'password'
    ])
    
    # Ejemplos
    writer.writerow([
        'estudiante@ejemplo.com',
        'Juan',
        'Pérez',
        'Estudiante',
        '00112345678',
        '2010-05-15',
        'M',
        '809-555-1234',
        'Calle Principal #123',
        '5to',
        'A',
        '',
        '',
        '',
        'mi_contraseña_123'
    ])
    
    writer.writerow([
        'profesor@ejemplo.com',
        'María',
        'García',
        'Profesor',
        '40212345678',
        '1985-03-20',
        'F',
        '809-555-5678',
        'Av. Duarte #456',
        '',
        '',
        'Matemáticas',
        'Ciencias',
        '',
        'profesor123'
    ])
    
    writer.writerow([
        'secretaria@ejemplo.com',
        'Ana',
        'Rodríguez',
        'Secretaria',
        '00312345678',
        '1990-08-10',
        'F',
        '809-555-9012',
        'Calle Secundaria #789',
        '',
        '',
        '',
        'Administración',
        'Secretaria Académica',
        'secret123'
    ])
    
    return response
