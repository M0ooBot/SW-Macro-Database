#Requires -Version 7.0
<#
.SYNOPSIS
Compiles every packaged script and recipe with the pinned SW-Agent script contract.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$KitAssets,
    [Parameter(Mandatory)][string]$InteropDir
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$repo = Split-Path -Parent $PSScriptRoot
$version = (Get-Content -LiteralPath (Join-Path $repo 'kit.version') -Raw).Trim()
if ($version -notmatch '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$') {
    throw "kit.version must contain one numeric major.minor.patch version."
}
$assets = (Resolve-Path -LiteralPath $KitAssets).ProviderPath
$interop = (Resolve-Path -LiteralPath $InteropDir).ProviderPath
$archiveName = "SwAgent.Kit.Reference-$version.zip"
$wrapperName = "script-wrapper-$version.cs"
$kitName = 'SwAgent.Kit.dll'
$manifest = @{}
foreach ($line in Get-Content -LiteralPath (Join-Path $assets 'SHA256SUMS')) {
    if ($line -notmatch '^([a-fA-F0-9]{64}) +\*?([\w.-]+)$' -or $manifest.ContainsKey($Matches[2])) {
        throw 'Malformed or duplicate checksum in SHA256SUMS.'
    }
    $manifest[$Matches[2]] = $Matches[1]
}

function Assert-Checksum([string]$Path, [string]$Name) {
    $digest = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    if ($manifest[$Name] -ne $digest) {
        throw "SHA256SUMS does not match $Name for Kit $version."
    }
}

function Get-Interop([string]$Path, [string]$Name, [string]$Token) {
    $assembly = [Reflection.AssemblyName]::GetAssemblyName($path)
    $publicKeyToken = [Convert]::ToHexString($assembly.GetPublicKeyToken())
    if ($assembly.Name -cne $Name -or $assembly.Version.Major -ne 32 -or $publicKeyToken -ne $Token) {
        throw "$Name must be a SolidWorks 2024 interop assembly. Found $($assembly.FullName)."
    }
    return $assembly.Version
}

function Assert-KitReference([string]$Path) {
    $assembly = [Reflection.AssemblyName]::GetAssemblyName($Path)
    if ($assembly.Name -cne 'SwAgent.Kit' -or $assembly.Version -ne [version]"$version.0") {
        throw "Expected SwAgent.Kit assembly version $version.0. Found $($assembly.FullName)."
    }
    $reader = [System.Reflection.PortableExecutable.PEReader]::new([IO.File]::OpenRead($Path))
    try {
        $metadata = [System.Reflection.Metadata.PEReaderExtensions]::GetMetadataReader($reader)
        foreach ($handle in $metadata.GetAssemblyDefinition().GetCustomAttributes()) {
            $attribute = $metadata.GetCustomAttribute($handle)
            if ($attribute.Constructor.Kind -ne 'MemberReference') { continue }
            $member = [System.Reflection.Metadata.MemberReferenceHandle]::op_Explicit($attribute.Constructor)
            $parent = $metadata.GetMemberReference($member).Parent
            if ($parent.Kind -ne 'TypeReference') { continue }
            $type = $metadata.GetTypeReference([System.Reflection.Metadata.TypeReferenceHandle]::op_Explicit($parent))
            if ($metadata.GetString($type.Namespace) -ceq 'System.Runtime.CompilerServices' -and
                $metadata.GetString($type.Name) -ceq 'ReferenceAssemblyAttribute') {
                return
            }
        }
        throw "$kitName must be the exported reference assembly."
    }
    finally {
        $reader.Dispose()
    }
}

$archive = Join-Path $assets $archiveName
$wrapperFile = Join-Path $assets $wrapperName
Assert-Checksum $archive $archiveName
Assert-Checksum $wrapperFile $wrapperName
$utf8 = [Text.UTF8Encoding]::new($false, $true)
$template = [IO.File]::ReadAllText($wrapperFile, $utf8).ReplaceLineEndings("`n")
$marker = '// SWAGENT_SCRIPT_BODY'
$markerAt = $template.IndexOf($marker, [StringComparison]::Ordinal)
if ($markerAt -lt 0 -or $markerAt -ne $template.LastIndexOf($marker, [StringComparison]::Ordinal)) {
    throw "$wrapperName must have one script body marker."
}

# Use the .NET installation's own Roslyn and net10.0 reference pack. No project
# build or resolver may replace the reference paths via ambient MSBuild options.
$dotnet = (Get-Command dotnet -CommandType Application | Select-Object -First 1).Source
$sdks = & $dotnet --list-sdks | ForEach-Object {
    if ($_ -match '^(10\.0\.[0-9]+) \[([^\]]+)\]$') {
        [pscustomobject]@{ Version = [version]$Matches[1]; Path = Join-Path $Matches[2] $Matches[1] }
    }
}
$sdk = $sdks | Sort-Object Version -Descending | Select-Object -First 1
if (!$sdk) { throw 'Install a stable .NET 10 SDK before compiling recipes.' }
$csc = Join-Path $sdk.Path 'Roslyn/bincore/csc.dll'
$dotnetRoot = Split-Path -Parent (Split-Path -Parent $sdk.Path)
$packRoot = Join-Path $dotnetRoot 'packs/Microsoft.NETCore.App.Ref'
$framework = Get-ChildItem -LiteralPath $packRoot -Directory -Filter '10.0.*' |
    Where-Object { $_.Name -match '^10\.0\.[0-9]+$' } |
    Sort-Object { [version]$_.Name } -Descending | Select-Object -First 1
if (!$framework) { throw 'The .NET 10 SDK installation needs its net10.0 reference pack.' }
$frameworkRefs = Get-ChildItem -LiteralPath (Join-Path $framework.FullName 'ref/net10.0') -File -Filter '*.dll' |
    Sort-Object Name | Select-Object -ExpandProperty FullName

$sources = @(Get-ChildItem -LiteralPath (Join-Path $repo 'entries') -Filter '*.csx' -File -Recurse)
$sources += @(Get-ChildItem -LiteralPath (Join-Path $repo 'scripts') -Directory | ForEach-Object {
    $source = Join-Path $_.FullName 'script.csx'
    if (!(Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Missing script body in $($_.Name)."
    }
    Get-Item -LiteralPath $source
})

$temporaryRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$temp = [IO.Directory]::CreateTempSubdirectory('sw-recipe-compile-').FullName
try {
    $zip = [IO.Compression.ZipFile]::OpenRead($archive)
    try {
        if ($zip.Entries.Count -ne 1 -or $zip.Entries[0].FullName -cne $kitName) {
            throw "$archiveName must contain exactly $kitName."
        }
        $kit = Join-Path $temp $kitName
        [IO.Compression.ZipFileExtensions]::ExtractToFile($zip.Entries[0], $kit)
    }
    finally {
        $zip.Dispose()
    }
    Assert-Checksum $kit $kitName
    Assert-KitReference $kit

    $sldworks = Join-Path $temp 'SolidWorks.Interop.sldworks.dll'
    $swconst = Join-Path $temp 'SolidWorks.Interop.swconst.dll'
    Copy-Item -LiteralPath (Join-Path $interop 'SolidWorks.Interop.sldworks.dll') -Destination $sldworks
    Copy-Item -LiteralPath (Join-Path $interop 'SolidWorks.Interop.swconst.dll') -Destination $swconst
    $interopVersion = Get-Interop $sldworks 'SolidWorks.Interop.sldworks' '7c4797c3e4eeac03'
    if ($interopVersion -ne (Get-Interop $swconst 'SolidWorks.Interop.swconst' '19f43e188e4269d8')) {
        throw 'Use both interop assemblies from the same SolidWorks 2024 installation.'
    }

    $wrappedSource = Join-Path $temp 'Wrapped.cs'
    $compiled = Join-Path $temp 'Recipe.dll'
    $response = Join-Path $temp 'compile.rsp'
    $references = foreach ($path in @($frameworkRefs) + @($kit, $sldworks, $swconst)) {
        "/reference:`"$path`""
    }
    @(
        '/nologo', '/nostdlib+', '/target:library', '/langversion:14.0',
        '/nullable:disable', '/optimize-', '/deterministic+',
        "/out:`"$compiled`"", "`"$wrappedSource`""
    ) + $references | Set-Content -LiteralPath $response -Encoding utf8NoBOM

    # Check the contract itself even in a database with no script bodies.
    $emptyWrapper = $template.Remove($markerAt, $marker.Length)
    [IO.File]::WriteAllText($wrappedSource, $emptyWrapper, $utf8)
    $output = & $dotnet $csc /noconfig "@$response"
    if ($LASTEXITCODE -ne 0) {
        $output | Write-Host
        throw 'The exported script contract did not compile.'
    }

    $failed = [Collections.Generic.List[string]]::new()
    foreach ($source in ($sources | Sort-Object FullName)) {
        $relative = [IO.Path]::GetRelativePath($repo, $source.FullName)
        $body = [IO.File]::ReadAllText($source.FullName, $utf8)
        $wrapped = $emptyWrapper.Insert($markerAt, $body)
        [IO.File]::WriteAllText($wrappedSource, $wrapped, $utf8)
        # Rebuild each body independently. The wrapper declares the same entry point every time.
        $output = & $dotnet $csc /noconfig "@$response"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Could not compile $relative"
            $output | Write-Host
            $failed.Add($relative)
        } else {
            Write-Host "Compiled $relative"
        }
    }
    if ($failed.Count) { throw "Compilation failed: $($failed -join ', ')" }
    Write-Host "Compiled $($sources.Count) bodies with Kit $version and SolidWorks interop $interopVersion."
}
finally {
    $resolved = (Resolve-Path -LiteralPath $temp).ProviderPath
    $relativeTemp = [IO.Path]::GetRelativePath($temporaryRoot, $resolved)
    if ($relativeTemp -notmatch '^sw-recipe-compile-[^/\\]+$') {
        throw "Unexpected compiler temporary directory: $resolved"
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
