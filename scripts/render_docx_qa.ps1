param(
    [string]$DocxPath = "output/Local_Flora_Concise_Smartphone.docx",
    [string]$OutDir = "tmp/docx-qa"
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$workspaceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
if (-not [IO.Path]::IsPathRooted($DocxPath)) {
    $DocxPath = Join-Path $workspaceRoot $DocxPath
}
$DocxPath = [IO.Path]::GetFullPath($DocxPath)

if (-not [IO.Path]::IsPathRooted($OutDir)) {
    $OutDir = Join-Path $workspaceRoot $OutDir
}
$OutDir = [IO.Path]::GetFullPath($OutDir)
[void][IO.Directory]::CreateDirectory($OutDir)

if (-not (Test-Path -LiteralPath $DocxPath)) {
    throw "Target DOCX does not exist: $DocxPath"
}

Write-Output "Rendering QA visual layout for: $DocxPath"
Write-Output "Output directory: $OutDir"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.AutomationSecurity = 3
$document = $null

try {
    # Open document read-only to guarantee file preservation
    $document = $word.Documents.Open($DocxPath, $false, $true)
    
    # Export to PDF
    $pdfBase = [IO.Path]::GetFileNameWithoutExtension($DocxPath)
    $pdfPath = Join-Path $OutDir "$pdfBase.pdf"
    try {
        $document.ExportAsFixedFormat($pdfPath, 17) # wdExportFormatPDF = 17
        Write-Output "Exported PDF: $pdfPath"
    } catch {
        Write-Warning "Word PDF export encountered warning: $_"
    }

    # Render native page metafiles to PNG (page-1.png .. page-N.png)
    $pages = $document.ActiveWindow.Panes.Item(1).Pages
    $pageCount = $pages.Count
    Write-Output "Total document pages: $pageCount"
    
    for ($i = 1; $i -le $pageCount; $i++) {
        $stream = [IO.MemoryStream]::new([byte[]]$pages.Item($i).EnhMetaFileBits)
        $metafile = [Drawing.Imaging.Metafile]::new($stream)
        $bitmap = [Drawing.Bitmap]::new(1240, 1754)
        $graphics = [Drawing.Graphics]::FromImage($bitmap)
        try {
            $graphics.Clear([Drawing.Color]::White)
            $graphics.DrawImage($metafile, 0, 0, 1240, 1754)
            $pagePng = Join-Path $OutDir "page-$i.png"
            $bitmap.Save($pagePng, [Drawing.Imaging.ImageFormat]::Png)
            Write-Output "Generated page raster: page-$i.png"
        } finally {
            $graphics.Dispose()
            $bitmap.Dispose()
            $metafile.Dispose()
            $stream.Dispose()
        }
    }
    Write-Output "Page rasterization QA completed successfully: $pageCount pages."
} finally {
    if ($null -ne $document) {
        $document.Close(0)
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($document)
    }
    $word.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}

