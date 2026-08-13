param(
    [Parameter(Mandatory = $true)]
    [string]$AwsRegion,

    [Parameter(Mandatory = $true)]
    [string]$AwsAccountId,

    [Parameter(Mandatory = $false)]
    [string]$RepositoryName = "ventas-app",

    [Parameter(Mandatory = $false)]
    [string]$ImageTag = "latest"
)

$ErrorActionPreference = "Stop"

$ecrUri = "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com"
$imageUri = "$ecrUri/$RepositoryName:$ImageTag"

Write-Host "[1/5] Verificando repositorio ECR..."
aws ecr describe-repositories --repository-names $RepositoryName --region $AwsRegion *> $null
if ($LASTEXITCODE -ne 0) {
    aws ecr create-repository --repository-name $RepositoryName --region $AwsRegion | Out-Null
}

Write-Host "[2/5] Login en ECR..."
$loginPassword = aws ecr get-login-password --region $AwsRegion
$loginPassword | docker login --username AWS --password-stdin $ecrUri

Write-Host "[3/5] Build de imagen..."
docker build -t "$RepositoryName:$ImageTag" .

Write-Host "[4/5] Tag de imagen..."
docker tag "$RepositoryName:$ImageTag" $imageUri

Write-Host "[5/5] Push a ECR..."
docker push $imageUri

Write-Host "Imagen publicada: $imageUri"
