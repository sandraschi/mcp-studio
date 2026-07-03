; Kill UI + backend before install/uninstall (backend locks resources/*.exe).
!macro KillMcpStudioFleetProcesses
  DetailPrint "Stopping mcp-studio processes..."
  ExecWait 'taskkill /F /IM mcp-studio-backend.exe /T' $0
  ExecWait 'taskkill /F /IM mcp-studio-native.exe /T' $0
  !if "${INSTALLMODE}" == "currentUser"
    nsis_tauri_utils::KillProcessCurrentUser "mcp-studio-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcessCurrentUser "mcp-studio-native.exe"
    Pop $0
  !else
    nsis_tauri_utils::KillProcess "mcp-studio-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcess "mcp-studio-native.exe"
    Pop $0
  !endif
  Sleep 2000
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillMcpStudioFleetProcesses
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillMcpStudioFleetProcesses
!macroend

!macro NSIS_HOOK_POSTINSTALL
  IfFileExists "$INSTDIR\resources\install-mcp-clients.ps1" 0 mcp_hook_done
    DetailPrint "Optional: register mcp-studio in Cursor / Claude Desktop"
    ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\resources\install-mcp-clients.ps1" -Interactive'
  mcp_hook_done:
!macroend