#!/bin/bash
################################################################################
# Otomatik Deployment Script - Kritik Düzeltmeler
# Bash Wrapper for Python Deployment Script
################################################################################

set -e  # Hata durumunda dur

# Renkler
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║         KRİTİK HATALARIN OTOMATIK DEPLOYMENT                          ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Python kontrolü
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 bulunamadı!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python3 bulundu${NC}"
echo ""

# Script'i çalıştır
echo "Python deployment script'i başlatılıyor..."
echo ""

python3 scripts/deploy_critical_fixes.py "$@"

# Exit code'u aktar
exit $?