@ECHO OFF
SETLOCAL

SET PYTHONPATH="../..:%PYTHONPATH%"
python -m sllurp.stork -n 100 %*

ENDLOCAL
