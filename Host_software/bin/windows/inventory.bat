@ECHO OFF
SETLOCAL

SET PYTHONPATH="../..:%PYTHONPATH%"
python -m sllurp.inventory -n 100 -s 2 -P 32 -M WISP5 -X 20 %* 192.168.10.101

ENDLOCAL

pause 