[CmdletBinding()]
param(
 [string]$PythonPath='C:\Python314\python.exe',
 [switch]$CheckOnly
)
$ErrorActionPreference='Stop'
$root='C:\Program Files\RazerLite'
$data='C:\ProgramData\RazerLite'
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$principalCheck=New-Object Security.Principal.WindowsPrincipal($identity)
if (!$principalCheck.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Run PowerShell as Administrator from your desktop account.' }
if (!(Test-Path -LiteralPath $PythonPath -PathType Leaf)) { throw 'Python not found. Install 64-bit Python for all users, or pass -PythonPath.' }
$PythonPath=(Resolve-Path -LiteralPath $PythonPath).Path
$pythonw=Join-Path (Split-Path $PythonPath) 'pythonw.exe'
if (!(Test-Path -LiteralPath $pythonw -PathType Leaf)) { throw 'pythonw.exe is required beside python.exe.' }
& $PythonPath -c "import sys,struct;sys.exit(0 if sys.version_info >= (3,10) and struct.calcsize('P') == 8 else 1)"
if ($LASTEXITCODE -ne 0) { throw '64-bit Python 3.10 or newer is required.' }
$files=@('hardware.py','service.py','session.py','color_cycle.py','color_worker.py','mouse_binding.py','restore_button.py','config.json','install.ps1','restore.ps1','LICENSE','THIRD_PARTY.md','README.md','README.ru.md','CHANGELOG.md','VERSION')
foreach($file in $files) { if (!(Test-Path -LiteralPath (Join-Path $PSScriptRoot $file))) { throw "Missing release file: $file" } }
if (!(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'vendor\openrazer_win'))) { throw 'Missing vendor directory.' }
if ($CheckOnly) { Write-Output 'Preflight passed; no services, tasks or files changed.'; return }
if (Get-Service RazerLite -ErrorAction SilentlyContinue) { throw 'RazerLite already installed; restore first to preserve the original backup.' }
New-Item -ItemType Directory -Force $root | Out-Null
if ((Resolve-Path $PSScriptRoot).Path -ne (Resolve-Path $root).Path) {
 foreach($file in $files) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot $file) -Destination $root -Force }
 Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'vendor') -Destination $root -Recurse -Force
}
New-Item -ItemType Directory -Force "$data\session" | Out-Null
$backup=Join-Path $data ('backup-'+(Get-Date -Format yyyyMMdd-HHmmss))
New-Item -ItemType Directory -Force $backup | Out-Null
$services=Get-CimInstance Win32_Service | Where-Object { $_.Name -match 'Razer|Chroma' -and $_.Name -ne 'RazerLite' }
ConvertTo-Json -InputObject @($services | Select-Object Name,StartMode,State) | Set-Content "$backup\services.json"
$tasks=Get-ScheduledTask | Where-Object { $_.TaskName -match 'Razer|Chroma' -and $_.TaskName -notlike 'RazerLite*' }
ConvertTo-Json -InputObject @($tasks | Select-Object TaskName,TaskPath,State) | Set-Content "$backup\tasks.json"
$run='HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$entries=@()
if (Test-Path $run) { (Get-Item $run).Property | ForEach-Object {
 $value=Get-ItemPropertyValue $run $_
 if ($value -match 'Razer|Chroma') { $entries+=@{Name=$_;Value=$value} }
}
}
ConvertTo-Json -InputObject @($entries) | Set-Content "$backup\run.json"
$backup | Set-Content "$data\last-backup.txt"
@{PythonPath=$PythonPath} | ConvertTo-Json | Set-Content "$data\installation.json"
foreach($entry in $entries) { Remove-ItemProperty $run $entry.Name }
foreach($t in $tasks) { Disable-ScheduledTask -TaskName $t.TaskName -TaskPath $t.TaskPath | Out-Null; Stop-ScheduledTask -TaskName $t.TaskName -TaskPath $t.TaskPath }
foreach($s in $services) { & sc.exe stop $s.Name | Out-Null; $svc=Get-Service $s.Name; try {$svc.WaitForStatus('Stopped',[TimeSpan]::FromSeconds(15))} catch { $live=Get-CimInstance Win32_Service | Where-Object Name -eq $s.Name; if($live.ProcessId -gt 0) {Stop-Process -Id $live.ProcessId -Force} }; Set-Service -Name $s.Name -StartupType Disabled }
Get-Process | Where-Object { $_.Path -and ($_.Path -like 'C:\Program Files\Razer\*' -or $_.Path -like 'C:\Program Files (x86)\Razer\*' -or $_.Path -like 'C:\Program Files (x86)\Razer Chroma SDK\*' -or $_.Path -like '*\Razer\RazerAppEngine\*') } | Stop-Process -Force
& icacls "$data\session" /grant ('{0}:(OI)(CI)M' -f $identity.Name) | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not set session directory permissions.' }
if (!(Get-Service RazerLite -ErrorAction SilentlyContinue)) {
 New-Service -Name RazerLite -DisplayName 'RazerLite - static lighting and maximum DPI' -BinaryPathName ('"{0}" "{1}\service.py"' -f $PythonPath,$root) -StartupType Automatic | Out-Null
}
& sc.exe failure RazerLite reset= 86400 actions= restart/5000/restart/15000/restart/60000 | Out-Null
$user=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$action=New-ScheduledTaskAction -Execute $pythonw -Argument '"C:\Program Files\RazerLite\session.py"' -WorkingDirectory $root
$trigger=New-ScheduledTaskTrigger -AtLogOn -User $user
$principal=New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest
$settings=New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName RazerLiteSession -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
Start-Service RazerLite
Start-ScheduledTask RazerLiteSession
$backup | Set-Content "$data\last-backup.txt"
Write-Output "Installed. Backup: $backup"
