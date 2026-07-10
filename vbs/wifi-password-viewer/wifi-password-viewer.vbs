' WiFi Password Viewer
' Shows all saved WiFi network names and passwords.
' Zero dependencies -- uses built-in netsh and VBScript.
' Just double-click to run.

Option Explicit

Dim objShell, objFSO, objWMI, colProfiles
Dim strOutput, strProfileName, strPassword, strAuth
Dim strCmd, objExec, strLine, arrLines, i
Dim strFilePath, objFile

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strOutput = "=== Saved WiFi Passwords ===" & vbCrLf & vbCrLf

' Get all saved WiFi profiles
Dim strProfilesCmd, strProfilesOutput
strProfilesCmd = "netsh wlan show profiles"
strProfilesOutput = RunCommand(strProfilesCmd)

' Parse profile names from output
Dim arrProfileLines, strProfileLine
Dim arrProfiles()
Dim profileCount
profileCount = 0

arrProfileLines = Split(strProfilesOutput, vbCrLf)

For i = 0 To UBound(arrProfileLines)
    strProfileLine = Trim(arrProfileLines(i))

    ' Profile lines look like: "    All User Profile     : NetworkName"
    If InStr(strProfileLine, "All User Profile") > 0 Or InStr(strProfileLine, "User Profile") > 0 Then
        If InStr(strProfileLine, ":") > 0 Then
            strProfileName = Trim(Split(strProfileLine, ":")(1))
            If strProfileName <> "" Then
                ReDim Preserve arrProfiles(profileCount)
                arrProfiles(profileCount) = strProfileName
                profileCount = profileCount + 1
            End If
        End If
    End If
Next

' If no profiles found, show message
If profileCount = 0 Then
    MsgBox "No saved WiFi profiles found.", 48, "WiFi Password Viewer"
    WScript.Quit
End If

' Get password for each profile
Dim strProfileDetail, strDetailCmd, strDetailOutput
Dim arrDetailLines, strDetailLine

For i = 0 To profileCount - 1
    strProfileName = arrProfiles(i)

    ' Get profile details including password
    strDetailCmd = "netsh wlan show profile """ & strProfileName & """ key=clear"
    strDetailOutput = RunCommand(strDetailCmd)

    ' Extract authentication type
    strAuth = ""
    arrDetailLines = Split(strDetailOutput, vbCrLf)
    Dim j
    For j = 0 To UBound(arrDetailLines)
        strDetailLine = Trim(arrDetailLines(j))
        If InStr(strDetailLine, "Authentication") > 0 And InStr(strDetailLine, ":") > 0 Then
            strAuth = Trim(Split(strDetailLine, ":")(1))
            Exit For
        End If
    Next

    ' Extract password (Key Content)
    strPassword = ""
    For j = 0 To UBound(arrDetailLines)
        strDetailLine = Trim(arrDetailLines(j))
        If InStr(strDetailLine, "Key Content") > 0 And InStr(strDetailLine, ":") > 0 Then
            strPassword = Trim(Split(strDetailLine, ":")(1))
            Exit For
        End If
    Next

    ' Build output line
    If strPassword <> "" Then
        strOutput = strOutput & "Network: " & strProfileName & vbCrLf
        strOutput = strOutput & "Password: " & strPassword & vbCrLf
        If strAuth <> "" Then
            strOutput = strOutput & "Security: " & strAuth & vbCrLf
        End If
        strOutput = strOutput & vbCrLf
    Else
        strOutput = strOutput & "Network: " & strProfileName & vbCrLf
        strOutput = strOutput & "Password: (hidden or open network)" & vbCrLf
        If strAuth <> "" Then
            strOutput = strOutput & "Security: " & strAuth & vbCrLf
        End If
        strOutput = strOutput & vbCrLf
    End If
Next

' Show results in message box
MsgBox strOutput, 64, "WiFi Password Viewer"

' Also save to Desktop
Dim strDesktop, strSavePath
strDesktop = objShell.SpecialFolders("Desktop")
strSavePath = strDesktop & "\wifi-passwords.txt"

Set objFile = objFSO.CreateTextFile(strSavePath, True)
objFile.Write strOutput
objFile.Close

MsgBox "Results also saved to:" & vbCrLf & strSavePath, 64, "WiFi Password Viewer"

' Cleanup
Set objShell = Nothing
Set objFSO = Nothing

' ============================================================
' Helper: Run a command and return its output
' ============================================================
Function RunCommand(cmd)
    Dim objExec, strOutput, strChar
    Set objExec = objShell.Exec("cmd /c " & cmd)
    strOutput = ""

    Do While Not objExec.StdOut.AtEndOfStream
        strChar = objExec.StdOut.Read(1)
        strOutput = strOutput & strChar
    Loop

    RunCommand = strOutput
End Function
