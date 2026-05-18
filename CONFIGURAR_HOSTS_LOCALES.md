# Configuración de hosts locales para testing multi-tenant

## Windows (requiere permisos de Administrador)

### Paso 1: Editar archivo hosts
1. Abre **Bloc de notas como Administrador**
2. Abre el archivo: `C:\Windows\System32\drivers\etc\hosts`
3. Agrega estas líneas al final:

```
127.0.0.1 cced.localhost
127.0.0.1 colegioevangelico.localhost
127.0.0.1 prueba.localhost
127.0.0.1 politecnicojoseramon.localhost
```

4. Guarda el archivo

### Paso 2: Probar en el navegador
- **Escuela de Prueba**: http://prueba.localhost:8000
- **CCED**: http://cced.localhost:8000
- **Colegio Evangélico**: http://colegioevangelico.localhost:8000
- **Politécnico**: http://politecnicojoseramon.localhost:8000

### Paso 3: Iniciar sesión
Cada escuela verá SOLO sus datos. El middleware detecta el subdominio y filtra automáticamente.

## ¿Cómo funciona?

1. **Usuario accede a**: `cced.localhost:8000`
2. **TenantMiddleware** detecta subdominio `cced`
3. **Busca escuela** con `nombre_corto='cced'`
4. **Establece contexto**: `request.escuela = Escuela(cced)`
5. **TenantQuerySetMiddleware** configura `tenant_context.current_escuela`
6. **TenantManager** filtra TODAS las queries por esa escuela

## Resultado:
- Usuario de CCED solo ve datos de CCED
- Usuario de Prueba solo ve datos de Prueba
- ¡Aislamiento total!

## Ventajas de este diseño:
✅ Más simple que schemas separados
✅ Un solo backup
✅ Migraciones aplicanpara todos
✅ Mejor rendimiento (un pool de conexiones)
✅ Escalable a miles de escuelas

## Desventajas:
⚠️ No es separación física (pero el filtrado es automático)
⚠️ Un error en el código podría exponer datos (pero los managers previenen esto)
