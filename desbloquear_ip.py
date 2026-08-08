#!/usr/bin/env python
"""
Script para desbloquear IP y limpiar rate limiting
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.core.cache import cache
from ventasweb.models import IPBlocklist


def desbloquear_ip(ip_address=None):
    """
    Desbloquea una IP específica o todas las IPs
    """
    if not ip_address:
        # Limpiar TODAS las IPs bloqueadas del caché
        cache_keys = [
            'rate_limit:login:*',
            'rate_limit:api:*',
            'rate_limit:general:*'
        ]
        
        print("🧹 Limpiando caché de rate limiting...")
        cache.clear()
        print("✅ Caché limpiado completamente")
        
        # Desbloquear todas las IPs temporales de la base de datos
        print("\n🔓 Desbloqueando IPs temporales de la base de datos...")
        bloqueadas = IPBlocklist.objects.filter(es_temporal=True)
        count = bloqueadas.count()
        bloqueadas.delete()
        print(f"✅ {count} IPs desbloqueadas de la base de datos")
        
    else:
        # Limpiar IP específica del caché
        print(f"🧹 Limpiando rate limiting para IP: {ip_address}")
        
        cache_keys = [
            f'rate_limit:login:{ip_address}',
            f'rate_limit:api:{ip_address}',
            f'rate_limit:general:{ip_address}'
        ]
        
        for key in cache_keys:
            cache.delete(key)
        
        print("✅ Caché limpiado para esta IP")
        
        # Desbloquear de la base de datos
        print(f"\n🔓 Desbloqueando IP de la base de datos: {ip_address}")
        bloqueadas = IPBlocklist.objects.filter(ip_address=ip_address)
        
        if bloqueadas.exists():
            count = bloqueadas.count()
            bloqueadas.delete()
            print(f"✅ IP desbloqueada ({count} registro(s) eliminado(s))")
        else:
            print("ℹ️  Esta IP no estaba bloqueada en la base de datos")
    
    print("\n" + "="*60)
    print("✅ PROCESO COMPLETADO")
    print("="*60)
    print("\nAhora puedes:")
    print("1. Refrescar tu navegador")
    print("2. Acceder normalmente al sistema")
    print(f"\nNuevos límites configurados:")
    print("  • Login: 20 requests/minuto (antes: 5)")
    print("  • API: 2000 requests/minuto (antes: 100)")
    print("  • General: 5000 requests/minuto (antes: 500)")
    print("\nTiempos de bloqueo reducidos:")
    print("  • Login: 15 minutos (antes: 30)")
    print("  • API: 10 minutos (antes: 15)")
    print("  • General: 5 minutos (antes: 10)")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        ip = sys.argv[1]
        print(f"Desbloqueando IP específica: {ip}")
        desbloquear_ip(ip)
    else:
        print("Desbloqueando TODAS las IPs...")
        print("\nUso:")
        print(f"  python {os.path.basename(__file__)}           # Desbloquear todas las IPs")
        print(f"  python {os.path.basename(__file__)} 127.0.0.1 # Desbloquear IP específica")
        print("\n" + "="*60)
        
        respuesta = input("\n¿Desbloquear TODAS las IPs? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'y', 'yes']:
            desbloquear_ip()
        else:
            print("❌ Operación cancelada")
