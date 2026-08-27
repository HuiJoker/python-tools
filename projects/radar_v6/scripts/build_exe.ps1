param(
    [string]$Python = "python"
)

Set-Location $PSScriptRoot\..
& $Python -m PyInstaller --noconfirm --windowed --onefile --name "员工能力雷达图V6" --paths src src/radar_v6/__main__.py
