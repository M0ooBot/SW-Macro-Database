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

function Get-Interop([string]$Name, [string]$Token) {
    $path = Join-Path $interop "$Name.dll"
    $assembly = [Reflection.AssemblyName]::GetAssemblyName($path)
    $publicKeyToken = [Convert]::ToHexString($assembly.GetPublicKeyToken())
    if ($assembly.Name -cne $Name -or $assembly.Version.Major -ne 32 -or $publicKeyToken -ne $Token) {
        throw "$Name must be a SolidWorks 2024 interop assembly. Found $($assembly.FullName)."
    }
    return @{ Path = $path; Version = $assembly.Version }
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

$sldworks = Get-Interop 'SolidWorks.Interop.sldworks' '7c4797c3e4eeac03'
$swconst = Get-Interop 'SolidWorks.Interop.swconst' '19f43e188e4269d8'
if ($sldworks.Version -ne $swconst.Version) {
    throw 'Use both interop assemblies from the same SolidWorks 2024 installation.'
}
$interopRefs = @($sldworks.Path, $swconst.Path)

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

    $references = foreach ($path in @($kit) + $interopRefs) {
        $name = [IO.Path]::GetFileNameWithoutExtension($path)
        $escapedPath = [Security.SecurityElement]::Escape($path)
        "<Reference Include='$name'><HintPath>$escapedPath</HintPath><Private>false</Private></Reference>"
    }
    $project = Join-Path $temp 'Compile.csproj'
    $wrappedSource = Join-Path $temp 'Wrapped.cs'
    @"
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <LangVersion>14.0</LangVersion>
    <ImplicitUsings>disable</ImplicitUsings>
    <Nullable>disable</Nullable>
    <EnableDefaultItems>false</EnableDefaultItems>
    <EnableNETAnalyzers>false</EnableNETAnalyzers>
    <Optimize>false</Optimize>
  </PropertyGroup>
  <ItemGroup>
    <Compile Include="Wrapped.cs" />
    $references
  </ItemGroup>
</Project>
"@ | Set-Content -LiteralPath $project -Encoding utf8NoBOM
    $nuget = Join-Path $temp 'NuGet.Config'
    '<configuration><packageSources><clear /></packageSources></configuration>' |
        Set-Content -LiteralPath $nuget -Encoding utf8NoBOM
    # Check the contract itself even in a database with no script bodies.
    [IO.File]::WriteAllText($wrappedSource, $template.Remove($markerAt, $marker.Length), $utf8)
    $output = dotnet build $project --configfile $nuget --nologo --verbosity quiet
    if ($LASTEXITCODE -ne 0) {
        $output | Write-Host
        throw 'The exported script contract did not compile.'
    }

    $failed = [Collections.Generic.List[string]]::new()
    foreach ($source in ($sources | Sort-Object FullName)) {
        $relative = [IO.Path]::GetRelativePath($repo, $source.FullName)
        $body = [IO.File]::ReadAllText($source.FullName, $utf8)
        $wrapped = $template.Remove($markerAt, $marker.Length).Insert($markerAt, $body)
        [IO.File]::WriteAllText($wrappedSource, $wrapped, $utf8)
        # Rebuild each body independently. The wrapper declares the same entry point every time.
        $output = dotnet build $project --no-restore --target Rebuild --nologo --verbosity quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Could not compile $relative"
            $output | Write-Host
            $failed.Add($relative)
        } else {
            Write-Host "Compiled $relative"
        }
    }
    if ($failed.Count) { throw "Compilation failed: $($failed -join ', ')" }
    Write-Host "Compiled $($sources.Count) bodies with Kit $version and SolidWorks interop $($sldworks.Version)."
}
finally {
    $resolved = (Resolve-Path -LiteralPath $temp).ProviderPath
    $relativeTemp = [IO.Path]::GetRelativePath($temporaryRoot, $resolved)
    if ($relativeTemp -notmatch '^sw-recipe-compile-[^/\\]+$') {
        throw "Unexpected compiler temporary directory: $resolved"
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
