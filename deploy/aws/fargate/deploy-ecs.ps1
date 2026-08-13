param(
    [Parameter(Mandatory = $true)]
    [string]$AwsRegion,

    [Parameter(Mandatory = $true)]
    [string]$ClusterName,

    [Parameter(Mandatory = $true)]
    [string]$ServiceName,

    [Parameter(Mandatory = $true)]
    [string]$TaskDefinitionFile
)

$ErrorActionPreference = "Stop"

Write-Host "Registrando nueva revision de task definition..."
$registerOutput = aws ecs register-task-definition --region $AwsRegion --cli-input-json file://$TaskDefinitionFile
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo registrar task definition"
}

$taskDefArn = ($registerOutput | ConvertFrom-Json).taskDefinition.taskDefinitionArn
Write-Host "Task definition registrada: $taskDefArn"

Write-Host "Actualizando servicio ECS..."
aws ecs update-service `
    --region $AwsRegion `
    --cluster $ClusterName `
    --service $ServiceName `
    --task-definition $taskDefArn `
    --force-new-deployment | Out-Null

Write-Host "Despliegue iniciado en servicio: $ServiceName"
