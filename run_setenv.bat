@echo off

echo Initializing VideoFactory...

rem Delay for 2 seconds
timeout /t 2 > nul

echo ----------------------------
echo.
echo VideoFactory initialized successfully.
echo --------------------------------------
echo.

rem Run the main.py script with --option 6 (Set Environment Variables)
python main.py --option 6