# COMANDO DE GESTIÓN: REGISTRAR SALIDAS AUTOMÁTICAS

Este comando registra automáticamente las salidas a las 4:00 PM para estudiantes y personal que poncharon entrada pero no registraron salida.

## Uso Manual

### Comando básico (registra salidas a las 4:00 PM para hoy):
```bash
python manage.py registrar_salidas_automaticas
```

### Especificar hora diferente:
```bash
python manage.py registrar_salidas_automaticas --hora 17:00
```

### Procesar una fecha específica:
```bash
python manage.py registrar_salidas_automaticas --fecha 2026-01-14
```

### Ver qué haría sin aplicar cambios (dry run):
```bash
python manage.py registrar_salidas_automaticas --dry-run
```

### Combinación de opciones:
```bash
python manage.py registrar_salidas_automaticas --hora 16:30 --fecha 2026-01-13 --dry-run
```

## Configuración Automática

### Windows (Programador de Tareas)

1. **Abrir el Programador de Tareas**:
   - Presiona `Win + R`, escribe `taskschd.msc` y presiona Enter

2. **Crear Tarea Básica**:
   - Clic derecho en "Biblioteca del Programador de tareas" → "Crear tarea básica"
   - Nombre: "Registrar Salidas Escolares Automáticas"
   - Descripción: "Registra salidas a las 4:00 PM para estudiantes y personal"

3. **Configurar Desencadenador**:
   - Iniciar la tarea: "Diariamente"
   - Hora: 16:00 (4:00 PM)
   - Repetir: Todos los días

4. **Configurar Acción**:
   - Acción: "Iniciar un programa"
   - Programa/script: `E:\Escuela_backup\Escuela\registrar_salidas.bat`
   - Iniciar en: `E:\Escuela_backup\Escuela`

5. **Configuraciones adicionales**:
   - Pestaña "General": Marcar "Ejecutar con los privilegios más altos"
   - Pestaña "Condiciones": Desmarcar "Iniciar la tarea solo si el equipo está conectado a alimentación de CA"
   - Pestaña "Configuración": Marcar "Ejecutar la tarea lo antes posible después de un inicio programado perdido"

### Linux/AWS EC2 (Crontab)

1. **Editar crontab**:
   ```bash
   crontab -e
   ```

2. **Agregar línea** (ejecutar a las 4:00 PM todos los días):
   ```bash
   0 16 * * * cd /ruta/al/proyecto && /ruta/al/proyecto/.venv/bin/python manage.py registrar_salidas_automaticas >> /var/log/salidas_automaticas.log 2>&1
   ```

3. **Ejemplo específico**:
   ```bash
   0 16 * * * cd /home/ubuntu/Escuela && /home/ubuntu/Escuela/.venv/bin/python manage.py registrar_salidas_automaticas >> /home/ubuntu/logs/salidas_automaticas.log 2>&1
   ```

4. **Verificar crontab**:
   ```bash
   crontab -l
   ```

### Explicación del formato cron:
```
# ┌─────────── minuto (0 - 59)
# │ ┌───────── hora (0 - 23)
# │ │ ┌─────── día del mes (1 - 31)
# │ │ │ ┌───── mes (1 - 12)
# │ │ │ │ ┌─── día de la semana (0 - 7) (domingo = 0 o 7)
# │ │ │ │ │
  0 16 * * *  → A las 4:00 PM todos los días
```

## Ejemplos de Horarios

```bash
# Lunes a viernes a las 4:00 PM
0 16 * * 1-5

# Todos los días a las 5:00 PM
0 17 * * *

# Todos los días a las 4:30 PM
30 16 * * *
```

## Logs y Monitoreo

### Crear carpeta de logs:
```bash
mkdir logs
```

### Ejecutar con log:
```bash
python manage.py registrar_salidas_automaticas >> logs/salidas_automaticas.log 2>&1
```

### Ver últimos logs:
```bash
# Windows PowerShell
Get-Content logs\salidas_automaticas.log -Tail 50

# Linux
tail -f logs/salidas_automaticas.log
```

## Pruebas

### Prueba 1: Ver qué haría sin aplicar cambios
```bash
python manage.py registrar_salidas_automaticas --dry-run
```

### Prueba 2: Procesar día anterior
```bash
python manage.py registrar_salidas_automaticas --fecha 2026-01-13
```

### Prueba 3: Usar hora diferente
```bash
python manage.py registrar_salidas_automaticas --hora 15:00 --dry-run
```

## Notas Importantes

1. **Zona Horaria**: El comando usa la zona horaria configurada en `settings.py` (America/Santo_Domingo)

2. **Solo actualiza registros existentes**: Solo procesa registros que ya tienen hora de entrada pero no tienen hora de salida

3. **No crea nuevos registros**: Si alguien no ponchó entrada, no se le creará un registro

4. **Idempotente**: Se puede ejecutar múltiples veces sin duplicar registros

5. **AWS/Producción**: Asegúrate de que el cron job use el usuario correcto y las rutas absolutas

## Troubleshooting

### El comando no se encuentra:
```bash
python manage.py help  # Verificar que Django esté funcionando
python manage.py registrar_salidas_automaticas --help  # Ver ayuda del comando
```

### Problemas de permisos en Linux:
```bash
chmod +x registrar_salidas.sh
```

### Ver logs de cron en Linux:
```bash
grep CRON /var/log/syslog
```
