param(
    [string]$Python = "python"
)

Set-Location "$PSScriptRoot\.."
$env:PYTHONPATH = "src"
& $Python -m radar_v6
