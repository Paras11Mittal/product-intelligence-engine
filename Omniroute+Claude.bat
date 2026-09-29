@echo off
TITLE Claude Code Environment
echo [1/3] Starting OmniRoute server in a separate window...
:: This opens a new command prompt window to run the server
start "OmniRoute Server" cmd /k "omniroute"
echo [2/3] Waiting 3 seconds for the server to initialize...
timeout /t 3 /nobreak > nul
echo [3/3] Setting temporary environment variables...
:: These variables only exist while this specific window is open
set CLAUDE_CONFIG_DIR=%USERPROFILE%\.claude-omniroute
set ANTHROPIC_BASE_URL=http://localhost:20128
set ANTHROPIC_AUTH_TOKEN=sk-e2d04cdac73e3781-461c94-d8b8ed6d
set ANTHROPIC_API_KEY=ignored
set ANTHROPIC_MODEL=Titan
echo Launching Claude Code...
claude