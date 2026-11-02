#!/usr/bin/env bash
# Orijinal repodan veri dosyalarını indirir (Raissi et al., MIT lisansı)
set -e
cd "$(dirname "$0")"
BASE=https://github.com/maziarraissi/PINNs/raw/master
[ -f burgers_shock.mat ] || curl -L -o burgers_shock.mat "$BASE/appendix/Data/burgers_shock.mat"
[ -f cylinder_nektar_wake.mat ] || curl -L -o cylinder_nektar_wake.mat "$BASE/main/Data/cylinder_nektar_wake.mat"
echo "Veri hazır."
