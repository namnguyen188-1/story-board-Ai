Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

portablePythonw = currentDir & "\studio\runtime\python\pythonw.exe"
venvPythonw = currentDir & "\studio\.venv\Scripts\pythonw.exe"
desktopScript = currentDir & "\studio\desktop_app.py"

If fso.FileExists(portablePythonw) Then
    pythonwExe = portablePythonw
ElseIf fso.FileExists(venvPythonw) Then
    pythonwExe = venvPythonw
Else
    MsgBox "Không tìm thấy môi trường Python (runtime hoặc .venv):" & vbCrLf & portablePythonw, vbCritical, "Storyboard AI Studio Pro"
    WScript.Quit 1
End If

WshShell.CurrentDirectory = currentDir
WshShell.Run """" & pythonwExe & """ """ & desktopScript & """", 1, False
