@echo off
setlocal EnableExtensions EnableDelayedExpansion
where mcs >nul 2>&1 && (
    call :run_mcs %*
    exit /b !ERRORLEVEL!
)
if defined PYTHON if exist "%PYTHON%" (
    call :run_python "%PYTHON%" %*
    exit /b !ERRORLEVEL!
)
for %%P in (313 312 311 310) do (
    if exist "C:\Python%%P\python.exe" (
        call :run_python "C:\Python%%P\python.exe" %*
        exit /b !ERRORLEVEL!
    )
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%P\python.exe" (
        call :run_python "%LOCALAPPDATA%\Programs\Python\Python%%P\python.exe" %*
        exit /b !ERRORLEVEL!
    )
    if exist "%PROGRAMFILES%\Python%%P\python.exe" (
        call :run_python "%PROGRAMFILES%\Python%%P\python.exe" %*
        exit /b !ERRORLEVEL!
    )
)
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
    call :run_python "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" %*
    exit /b !ERRORLEVEL!
)
where python >nul 2>&1 && (
    call :run_python python %*
    exit /b !ERRORLEVEL!
)
where py >nul 2>&1 && (
    call :run_py %*
    exit /b !ERRORLEVEL!
)
echo MCS compiler not found. Install minecraft-script ^(pip install -e .^) or set compilerPath in config/mcs-packs.json. 1>&2
exit /b 1

:run_mcs
set "ARGS="
:quote_mcs
if "%~1"=="" goto exec_mcs
set "ARGS=%ARGS% "%~1""
shift
goto quote_mcs
:exec_mcs
mcs %ARGS%
exit /b %ERRORLEVEL%

:run_python
set "PY=%~1"
shift
set "ARGS="
:quote_py
if "%~1"=="" goto exec_py
set "ARGS=%ARGS% "%~1""
shift
goto quote_py
:exec_py
"%PY%" -m minecraft_script %ARGS%
exit /b %ERRORLEVEL%

:run_py
set "ARGS="
:quote_py_launcher
if "%~1"=="" goto exec_py_launcher
set "ARGS=%ARGS% "%~1""
shift
goto quote_py_launcher
:exec_py_launcher
py -3 -m minecraft_script %ARGS%
exit /b %ERRORLEVEL%
