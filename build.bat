@echo off
echo ==========================================
echo    Compilando PakayVault con PyInstaller
echo ==========================================
echo.
echo [1/3] Instalando dependencias necesarias...
pip install -r requirements.txt
pip install pyinstaller
echo.
echo [2/3] Generando ejecutable standalone...
pyinstaller --noconfirm --onefile --console --name "PakayVault" --clean "pakayvault.py"
echo.
echo [3/3] Limpiando archivos temporales de compilacion...
rmdir /s /q build
del /q PakayVault.spec
echo.
echo ==========================================
echo    ¡Compilacion finalizada exitosamente!
echo    Tu ejecutable esta en la carpeta: dist\
echo ==========================================
pause
