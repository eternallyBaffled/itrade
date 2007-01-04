; itrade.nsi
;
; This script is based on example2.nsi
;-------------------------------------

; The name of the installer
Name "iTrade v0.4.5"

; The file to write
OutFile "itrade_0_4_5.exe"

; The default installation directory
InstallDir $PROGRAMFILES\iTrade

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\iTrade" "Install_Dir"
  
SetCompressor lzma

;--------------------------------

; Pages

Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------

; The stuff to install
Section "iTrade (required)"

  SectionIn RO
  
  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  
  ; Put file there
  File /r dist\*.*

; Write the installation path into the registry
  WriteRegStr HKLM SOFTWARE\iTrade "Install_Dir" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\iTrade" "DisplayName" "iTrade v0.4.5"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\iTrade" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\iTrade" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\iTrade" "NoRepair" 1
  WriteUninstaller "uninstall.exe"
  
SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\iTrade"
  CreateShortCut "$SMPROGRAMS\iTrade\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortCut "$SMPROGRAMS\iTrade\iTrade.lnk" "$INSTDIR\itrade.exe" "" "$INSTDIR\itrade.exe" 0
  
SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\iTrade"
  DeleteRegKey HKLM SOFTWARE\iTrade

  ; Remove files and uninstaller
  Delete $INSTDIR\alerts\*.*
  Delete $INSTDIR\cache\*.*
  Delete $INSTDIR\images\*.*
  Delete $INSTDIR\matplotlibdata\*.*
  Delete $INSTDIR\matplotlibdata\Matplotlib.nib\*.*
  Delete $INSTDIR\data\*.*
  Delete $INSTDIR\res\*.*
  Delete $INSTDIR\usrdata\*.*
  Delete $INSTDIR\*.*
  Delete $INSTDIR\uninstall.exe

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\iTrade\*.*"

  ; Remove directories used
  RMDir "$SMPROGRAMS\iTrade"
  RMDir "$INSTDIR\alerts"
  RMDir "$INSTDIR\cache"
  RMDir "$INSTDIR\images"
  RMDir "$INSTDIR\reports"
  RMDir "$INSTDIR\export"
  RMDir "$INSTDIR\import"
  RMDir "$INSTDIR\snapshots"
  RMDir "$INSTDIR\matplotlibdata\Matplotlib.nib"
  RMDir "$INSTDIR\matplotlibdata"
  RMDir "$INSTDIR\data"
  RMDir "$INSTDIR\res"
  RMDir "$INSTDIR\usrdata"
  RMDir "$INSTDIR"

SectionEnd
