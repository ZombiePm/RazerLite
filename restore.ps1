$ErrorActionPreference='Stop'
$data='C:\ProgramData\RazerLite'
$backup=(Get-Content "$data\last-backup.txt").Trim()
Stop-ScheduledTask RazerLiteSession -ErrorAction SilentlyContinue
Unregister-ScheduledTask RazerLiteSession -Confirm:$false -ErrorAction SilentlyContinue
Stop-Service RazerLite -ErrorAction SilentlyContinue
if (Test-Path "$data\installation.json") { $python=(Get-Content "$data\installation.json" -Raw | ConvertFrom-Json).PythonPath } else { $python='C:\Python314\python.exe' }
& $python 'C:\Program Files\RazerLite\restore_button.py'
if ($LASTEXITCODE -ne 0) {throw 'Button restore failed; connect mouse and retry'}
& sc.exe delete RazerLite
foreach($s in (Get-Content "$backup\services.json" -Raw | ConvertFrom-Json)) {
 $mode=@{Auto='Automatic';Manual='Manual';Disabled='Disabled'}[$s.StartMode]
 Set-Service $s.Name -StartupType $mode
 if($s.State -eq 'Running') {Start-Service $s.Name}
}
foreach($t in (Get-Content "$backup\tasks.json" -Raw | ConvertFrom-Json)) {
 if($t.State -ne 'Disabled') {Enable-ScheduledTask -TaskName $t.TaskName -TaskPath $t.TaskPath | Out-Null}
}
foreach($r in (Get-Content "$backup\run.json" -Raw | ConvertFrom-Json)) {
 if (!(Test-Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run')) { New-Item 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Force | Out-Null }
 Set-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' $r.Name $r.Value
}
Write-Output 'Razer startup restored. Sign out/in to restart its user interface.'
