param(
    [string]$Source = 'output\Local_Flora_PDF_Format_Updated.docx',
    [string]$Destination = 'output\Local_Flora_Equations_Corrected.docx'
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$workspaceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$sourcePath = [IO.Path]::GetFullPath((Join-Path $workspaceRoot $Source))
$destinationPath = [IO.Path]::GetFullPath((Join-Path $workspaceRoot $Destination))
if ($sourcePath -eq $destinationPath) { throw 'The original must be preserved.' }
$sourceHash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
$archive = [IO.Compression.ZipFile]::OpenRead($sourcePath)
try {
    $reader = New-Object IO.StreamReader($archive.GetEntry('word/document.xml').Open())
    try { $xml = New-Object Xml.XmlDocument; $xml.PreserveWhitespace = $true; $xml.LoadXml($reader.ReadToEnd()) } finally { $reader.Dispose() }
} finally { $archive.Dispose() }
$w = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
$m = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
$ns = New-Object Xml.XmlNamespaceManager($xml.NameTable)
$ns.AddNamespace('w', $w)
$ns.AddNamespace('m', $m)
$matches = @($xml.SelectNodes('//w:body/w:p', $ns) | Where-Object { ($_.SelectNodes('.//w:t', $ns).InnerText -join '') -like 'For species k, precision is Pk*GDR_m*' })
if ($matches.Count -ne 1) { throw 'Expected exactly one matching metrics paragraph.' }
$original = $matches[0]
$originalText = $original.SelectNodes('.//w:t', $ns).InnerText -join ''
$sourceMathCount = $xml.SelectNodes('//m:oMath', $ns).Count
function Math-Run([string]$text, [switch]$Plain) {
    $style = if ($Plain) { '<m:rPr><m:sty m:val="p"/></m:rPr>' } else { '' }
    '<m:r>' + $style + '<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/><w:sz w:val="20"/></w:rPr><m:t>' + [Security.SecurityElement]::Escape($text) + '</m:t></m:r>'
}
function Math-Sub([string]$base, [string]$sub, [switch]$Plain) {
    '<m:sSub><m:e>' + (Math-Run $base -Plain:$Plain) + '</m:e><m:sub>' + (Math-Run $sub) + '</m:sub></m:sSub>'
}
function Math-Fraction([string]$numerator, [string]$denominator) {
    '<m:f><m:fPr><m:type m:val="bar"/></m:fPr><m:num>' + $numerator + '</m:num><m:den>' + $denominator + '</m:den></m:f>'
}
function Math-Bracket([string]$inner) {
    '<m:d><m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/></m:dPr><m:e>' + $inner + '</m:e></m:d>'
}
function Body-Run([string]$text) {
    '<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="20"/></w:rPr><w:t xml:space="preserve">' + [Security.SecurityElement]::Escape($text) + '</w:t></w:r>'
}
function Native-Math([string]$inner) { '<m:oMath>' + $inner + '</m:oMath>' }
function Insert-Paragraph([string]$content, [switch]$Equation) {
    $paragraph = $original.CloneNode($false)
    $properties = $original.SelectSingleNode('w:pPr', $ns).CloneNode($true)
    $properties.SelectSingleNode('w:spacing', $ns).SetAttribute('lineRule', $w, 'atLeast') | Out-Null
    $properties.SelectSingleNode('w:spacing', $ns).SetAttribute('line', $w, $(if ($Equation) { '400' } else { '240' })) | Out-Null
    if ($Equation) {
        $properties.SelectSingleNode('w:ind', $ns).SetAttribute('firstLine', $w, '0') | Out-Null
        $properties.SelectSingleNode('w:jc', $ns).SetAttribute('val', $w, 'center') | Out-Null
        $properties.SelectSingleNode('w:spacing', $ns).SetAttribute('before', $w, '40') | Out-Null
        $properties.SelectSingleNode('w:spacing', $ns).SetAttribute('after', $w, '40') | Out-Null
    }
    [void]$paragraph.AppendChild($properties)
    $fragment = $xml.CreateDocumentFragment()
    $fragment.InnerXml = '<w:p xmlns:w="' + $w + '" xmlns:m="' + $m + '">' + $content + '</w:p>'
    foreach ($child in @($fragment.FirstChild.ChildNodes)) { [void]$paragraph.AppendChild($child.CloneNode($true)) }
    [void]$original.ParentNode.InsertBefore($paragraph, $original)
}
$tp = Math-Sub 'TP' 'k' -Plain
$fp = Math-Sub 'FP' 'k' -Plain
$fn = Math-Sub 'FN' 'k' -Plain
$fa = Math-Sub 'F' 'A,m'
$fb = Math-Sub 'F' 'B,m'
$plus = Math-Run '+'
$equals = Math-Run '='
$times = Math-Run ([string][char]0x00D7)
$difference = $fa + (Math-Run ([string][char]0x2212)) + $fb
Insert-Paragraph (Body-Run 'For species k, precision, recall, and per-class F1 are defined as follows:')
Insert-Paragraph (Native-Math ((Math-Sub 'P' 'k') + $equals + (Math-Fraction $tp ($tp + $plus + $fp)))) -Equation
Insert-Paragraph (Native-Math ((Math-Sub 'R' 'k') + $equals + (Math-Fraction $tp ($tp + $plus + $fn)))) -Equation
Insert-Paragraph (Native-Math ((Math-Sub 'F1' 'k' -Plain) + $equals + (Math-Fraction ((Math-Run '2') + $tp) ((Math-Run '2') + $tp + $plus + $fp + $plus + $fn)))) -Equation
Insert-Paragraph ((Body-Run 'Macro F1 averages the per-class F1 scores equally across all K = 10 species [24]. To quantify sensitivity to unseen plants, let ') + (Native-Math $fa) + (Body-Run ' be pipeline m''s Macro F1 under Protocol A and ') + (Native-Math $fb) + (Body-Run ' be its pooled out-of-fold Macro F1 under Protocol B. The absolute generalization gap, in percentage points, is'))
Insert-Paragraph (Native-Math ((Math-Sub 'Gap' 'm' -Plain) + $equals + (Math-Run '100') + $times + (Math-Bracket $difference))) -Equation
Insert-Paragraph (Body-Run 'and the Generalization Drop Rate is')
Insert-Paragraph (Native-Math ((Math-Sub 'GDR' 'm' -Plain) + $equals + (Math-Run '100') + $times + (Math-Fraction $difference $fa))) -Equation
[void]$original.ParentNode.RemoveChild($original)
if ($xml.SelectNodes('//m:oMath', $ns).Count -ne ($sourceMathCount + 7)) { throw 'Native equation count mismatch.' }
if ($xml.SelectNodes('//m:f', $ns).Count -ne 4) { throw 'Expected four stacked fractions.' }
Copy-Item -LiteralPath $sourcePath -Destination $destinationPath
$archive = [IO.Compression.ZipFile]::Open($destinationPath, [IO.Compression.ZipArchiveMode]::Update)
try {
    $archive.GetEntry('word/document.xml').Delete()
    $entry = $archive.CreateEntry('word/document.xml')
    $writer = New-Object IO.StreamWriter($entry.Open(), (New-Object Text.UTF8Encoding($false)))
    try { $xml.Save($writer) } finally { $writer.Dispose() }
} finally { $archive.Dispose() }
if ((Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash -ne $sourceHash) { throw 'Original document changed.' }
$qaDirectory = Join-Path $PSScriptRoot 'equation-qa'
[void][IO.Directory]::CreateDirectory($qaDirectory)
[pscustomobject]@{Source=$sourcePath; Destination=$destinationPath; OriginalSHA256=$sourceHash; NativeEquations=7; StackedFractions=4; OriginalMetricsParagraph=$originalText} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $qaDirectory 'repair-report.json') -Encoding UTF8
Write-Output "Saved corrected copy with seven native equations and four stacked fractions: $destinationPath"
