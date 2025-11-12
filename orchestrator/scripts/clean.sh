#!/bin/sh -e
set -x

# Script para limpiar archivos temporales y cache del proyecto

echo "🧹 Limpiando archivos temporales..."

# Eliminar archivos __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Eliminar archivos .pyc
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Eliminar archivos .pyo
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Eliminar archivos .pyd
find . -type f -name "*.pyd" -delete 2>/dev/null || true

# Eliminar directorios .pytest_cache
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# Eliminar directorios .ruff_cache
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

# Eliminar directorios .mypy_cache
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

# Eliminar archivos de cobertura
find . -type f -name ".coverage" -delete 2>/dev/null || true
find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".coverage.*" -exec rm -rf {} + 2>/dev/null || true

# Eliminar directorios build y dist
find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Eliminar archivos temporales de editores
find . -type f -name "*~" -delete 2>/dev/null || true
find . -type f -name "*.swp" -delete 2>/dev/null || true
find . -type f -name "*.swo" -delete 2>/dev/null || true
find . -type f -name ".DS_Store" -delete 2>/dev/null || true

# Eliminar logs temporales
find . -type f -name "*.log" -delete 2>/dev/null || true

echo "✅ Limpieza completada!"
