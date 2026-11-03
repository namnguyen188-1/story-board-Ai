Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

pythonwExe = currentDir & "\studio\.venv\Scripts\pythonw.exe"
desktopScript = currentDir & "\studio\desktop_app.py"

If Not fso.FileExists(pythonwExe) Then
    MsgBox "Không tìm thấy môi trường Python: " & vbCrLf & pythonwExe, vbCritical, "Storyboard AI Studio Pro"
    WScript.Quit 1
End If

WshShell.CurrentDirectory = currentDir
WshShell.Run """" & pythonwExe & """ """ & desktopScript & """", 0, False
