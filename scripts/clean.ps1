# Script para limpiar archivos temporales y cache del proyecto

Write-Host "🧹 Limpiando archivos temporales..." -ForegroundColor Cyan

# Eliminar directorios __pycache__
Write-Host "Eliminando __pycache__..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Eliminar archivos .pyc, .pyo, .pyd
Write-Host "Eliminando archivos .pyc, .pyo, .pyd..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Include "*.pyc", "*.pyo", "*.pyd" -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

# Eliminar directorios .pytest_cache
Write-Host "Eliminando .pytest_cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Filter ".pytest_cache" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Eliminar directorios .ruff_cache
Write-Host "Eliminando .ruff_cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Filter ".ruff_cache" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Eliminar directorios .mypy_cache
Write-Host "Eliminando .mypy_cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Filter ".mypy_cache" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Eliminar archivos de cobertura
Write-Host "Eliminando archivos de cobertura..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Include ".coverage", ".coverage.*" -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -Directory -Filter "htmlcov" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Eliminar directorios build, dist y egg-info
Write-Host "Eliminando build, dist, egg-info..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Include "build", "dist" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -Directory -Filter "*.egg-info" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Eliminar archivos temporales de editores
Write-Host "Eliminando archivos temporales de editores..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Include "*~", "*.swp", "*.swo", ".DS_Store" -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

# Eliminar logs temporales
Write-Host "Eliminando archivos .log..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Filter "*.log" -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "✅ Limpieza completada!" -ForegroundColor Green
