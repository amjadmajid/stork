@ECHO OFF
SETLOCAL

SET PYTHONPATH="../..:%PYTHONPATH%"
C:\python27\python.exe -m sllurp.reset %* 192.168.10.101 

ENDLOCAL

pause