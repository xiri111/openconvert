# 用 WPS COM 把 docx 导出为 PDF（不影响源文件），用于版式自检。
# 用法：pwsh -File tools/export_pdf.ps1 -InFile docs/DESIGN.docx -OutFile tools/_preview/DESIGN.pdf [-UpdateFields]
param(
    [Parameter(Mandatory = $true)][string]$InFile,
    [Parameter(Mandatory = $true)][string]$OutFile,
    [switch]$UpdateFields
)

$ErrorActionPreference = 'Stop'
$src = (Resolve-Path $InFile).Path
$outDir = Split-Path -Parent $OutFile
if ($outDir -and -not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
$dst = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $OutFile))
if (Test-Path $dst) { Remove-Item $dst -Force }

$app = New-Object -ComObject Kwps.Application
$app.Visible = $false
$app.DisplayAlerts = 0
try {
    $doc = $app.Documents.Open($src)
    if ($UpdateFields) {
        $doc.Fields.Update() | Out-Null
        foreach ($toc in $doc.TablesOfContents) { $toc.Update() | Out-Null }
    }
    $pages = $doc.ComputeStatistics(2)
    $doc.ExportAsFixedFormat($dst, 17)
    $doc.Close(0)
    Write-Output "pages=$pages pdf=$dst"
}
finally {
    $app.Quit()
}
