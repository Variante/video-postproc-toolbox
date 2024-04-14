@echo off
REM Set DaVinci Resolve scripting environment variables

REM Escape the % signs to keep them as part of the value instead of expanding them
setx RESOLVE_SCRIPT_API "%%PROGRAMDATA%%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting
setx RESOLVE_SCRIPT_LIB "C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll
setx PYTHONPATH "%%PYTHONPATH%%;%%PROGRAMDATA%%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules\

echo Environment variables have been set.
