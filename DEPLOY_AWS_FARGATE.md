# Despliegue en AWS Fargate (Serverless) - Paso a paso

Esta guia esta adaptada a este proyecto Django multi-tenant con Celery.

## 1. Arquitectura recomendada

- ECS Fargate con 3 servicios:
  - `ventas-web` (Gunicorn)
  - `ventas-worker` (Celery Worker)
  - `ventas-beat` (Celery Beat)
- ECR para imagen Docker
- RDS PostgreSQL (obligatorio para django-tenants)
- ElastiCache Redis (broker de Celery)
- ALB publico para `ventas-web`
- Route53 + ACM para dominio HTTPS
- SSM Parameter Store para secretos

## 2. Pre-requisitos locales

- AWS CLI v2 configurado (`aws configure`)
- Docker Desktop instalado
- Permisos IAM para ECS, ECR, RDS, ElastiCache, SSM, ALB, CloudWatch

## 3. Archivos ya preparados en este repo

- `Dockerfile`
- `docker/entrypoint.sh`
- `deploy/aws/fargate/env.fargate.example`
- `deploy/aws/fargate/taskdef-web.json`
- `deploy/aws/fargate/taskdef-worker.json`
- `deploy/aws/fargate/taskdef-beat.json`
- `deploy/aws/fargate/build-and-push.ps1`
- `deploy/aws/fargate/deploy-ecs.ps1`

## 4. Crear red base (VPC)

Crea o reutiliza una VPC con:
- 2 subnets publicas (ALB)
- 2 subnets privadas (ECS, RDS, Redis)
- NAT Gateway para salida a internet desde privadas

## 5. Crear RDS PostgreSQL

Recomendado:
- Motor: PostgreSQL 15+
- Multi-AZ opcional
- Security Group permitiendo 5432 desde SG de ECS

Guarda host, puerto, usuario y base de datos para variables `DB_*`.

## 6. Crear ElastiCache Redis

Recomendado:
- Redis OSS
- Misma VPC y subnets privadas
- Security Group permitiendo 6379 desde SG de ECS

URL esperada para Celery:
- `redis://HOST_REDIS:6379/0`

## 7. Guardar secretos en SSM Parameter Store

Ejemplos (ajusta region y cuenta):

```powershell
aws ssm put-parameter --name "/ventas/SECRET_KEY" --type "SecureString" --value "TU_SECRET" --overwrite --region us-east-1
aws ssm put-parameter --name "/ventas/DB_NAME" --type "SecureString" --value "ventas" --overwrite --region us-east-1
aws ssm put-parameter --name "/ventas/DB_USER" --type "SecureString" --value "ventas_user" --overwrite --region us-east-1
aws ssm put-parameter --name "/ventas/DB_PASSWORD" --type "SecureString" --value "TU_PASS" --overwrite --region us-east-1
aws ssm put-parameter --name "/ventas/DB_HOST" --type "SecureString" --value "host-rds" --overwrite --region us-east-1
aws ssm put-parameter --name "/ventas/DB_PORT" --type "SecureString" --value "5432" --overwrite --region us-east-1
aws ssm put-parameter --name "/ventas/CELERY_BROKER_URL" --type "SecureString" --value "redis://host-redis:6379/0" --overwrite --region us-east-1
```

## 8. Crear cluster ECS y logs

```powershell
aws ecs create-cluster --cluster-name ventas-cluster --region us-east-1
aws logs create-log-group --log-group-name /ecs/ventas-web --region us-east-1
aws logs create-log-group --log-group-name /ecs/ventas-worker --region us-east-1
aws logs create-log-group --log-group-name /ecs/ventas-beat --region us-east-1
```

## 9. Build y push de la imagen a ECR

```powershell
.\deploy\aws\fargate\build-and-push.ps1 -AwsRegion us-east-1 -AwsAccountId 123456789012 -RepositoryName ventas-app -ImageTag v1
```

Luego actualiza en los task definition el campo `image` con esa etiqueta.

## 10. Registrar task definitions

Ajusta primero en cada JSON:
- `executionRoleArn`
- `taskRoleArn`
- `image`
- ARNs de `secrets`
- `awslogs-region`

Registrar:

```powershell
aws ecs register-task-definition --region us-east-1 --cli-input-json file://deploy/aws/fargate/taskdef-web.json
aws ecs register-task-definition --region us-east-1 --cli-input-json file://deploy/aws/fargate/taskdef-worker.json
aws ecs register-task-definition --region us-east-1 --cli-input-json file://deploy/aws/fargate/taskdef-beat.json
```

## 11. Migraciones iniciales (una sola vez)

Ejecuta tarea one-off de migraciones con el task definition web y command override:

```powershell
aws ecs run-task `
  --region us-east-1 `
  --cluster ventas-cluster `
  --launch-type FARGATE `
  --task-definition ventas-web `
  --network-configuration "awsvpcConfiguration={subnets=[subnet-aaa,subnet-bbb],securityGroups=[sg-ecs],assignPublicIp=DISABLED}" `
  --overrides '{"containerOverrides":[{"name":"ventas-web","command":["sh","-c","python manage.py migrate_schemas --noinput && python manage.py collectstatic --noinput"]}]}'
```

## 12. Crear servicios ECS

- `ventas-web` con ALB target group puerto 8000
- `ventas-worker` sin ALB
- `ventas-beat` sin ALB

Escalado inicial recomendado:
- web: 2 tasks
- worker: 1 task
- beat: 1 task

## 13. Dominio y HTTPS

- Emite certificado en ACM para `tudominio.com` y `*.tudominio.com`
- Configura listener HTTPS en ALB
- En Route53 apunta `A/AAAA (Alias)` al ALB

## 14. Variables criticas para multi-tenant

- `ALLOWED_HOSTS=.tudominio.com,tudominio.com`
- `CSRF_TRUSTED_ORIGINS=https://tudominio.com,https://*.tudominio.com`

## 15. Actualizaciones de version

1. Build/push nueva imagen
2. Actualizar `image` en taskdef
3. Ejecutar script de despliegue por servicio:

```powershell
.\deploy\aws\fargate\deploy-ecs.ps1 -AwsRegion us-east-1 -ClusterName ventas-cluster -ServiceName ventas-web -TaskDefinitionFile deploy/aws/fargate/taskdef-web.json
.\deploy\aws\fargate\deploy-ecs.ps1 -AwsRegion us-east-1 -ClusterName ventas-cluster -ServiceName ventas-worker -TaskDefinitionFile deploy/aws/fargate/taskdef-worker.json
.\deploy\aws\fargate\deploy-ecs.ps1 -AwsRegion us-east-1 -ClusterName ventas-cluster -ServiceName ventas-beat -TaskDefinitionFile deploy/aws/fargate/taskdef-beat.json
```

## 16. Checklist rapido de validacion

- `/admin/` responde en HTTPS
- Login funciona
- Creacion/resolucion de tenant por dominio funciona
- Tareas Celery aparecen en logs de worker/beat
- `migrate_schemas` aplicado sin errores

## 17. Errores comunes

- `DisallowedHost`: revisar `ALLOWED_HOSTS`
- CSRF fail: revisar `CSRF_TRUSTED_ORIGINS`
- Worker sin procesar tareas: revisar `CELERY_BROKER_URL` y SG de Redis
- Falla de arranque por secretos: validar rutas y permisos IAM a SSM

