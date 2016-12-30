@ECHO OFF
SETLOCAL

SET PYTHONPATH="../..:%PYTHONPATH%"
python -m sllurp.stork -n 100 -s 2 -P 32 -M WISP5 -f ihex/run-wireless2.hex %* 192.168.10.101

ENDLOCAL

call inventory.bat
