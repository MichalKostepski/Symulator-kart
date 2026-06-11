Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptFolder = fso.GetParentFolderName(WScript.ScriptFullName)
projectRoot = fso.GetParentFolderName(scriptFolder)

If Not fso.FileExists(fso.BuildPath(projectRoot, "app\host_gui.py")) Then
    projectRoot = scriptFolder
End If

If Not fso.FileExists(fso.BuildPath(projectRoot, "app\host_gui.py")) Then
    MsgBox "Nie znaleziono folderu projektu. Plik VBS powinien byc w folderze uruchomienie albo w glownym folderze projektu.", 16, "Poker / Makao Hub"
    WScript.Quit 1
End If

shell.CurrentDirectory = projectRoot
shell.Run "%ComSpec% /c pyw -3 app\host_gui.py || pythonw app\host_gui.py || py -3 app\host_gui.py || python app\host_gui.py", 0, False
