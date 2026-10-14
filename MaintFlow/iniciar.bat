@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
  if errorlevel 1 goto erro
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto erro
echo Abra http://127.0.0.1:5000 no navegador.
.venv\Scripts\python.exe app.py
pause
exit /b
:erro
echo Nao foi possivel iniciar. Confira o Python e a conexao com a internet.
pause
exit /b 1
