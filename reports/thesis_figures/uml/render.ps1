# Renders every fig4_*.puml in this folder to PNG next to the thesis figures (reports/thesis_figures/).
# Needs Java and PlantUML; Graphviz for use case, class, component and deployment diagrams.
#   $env:PLANTUML_JAR = 'C:\path\plantuml.jar'; $env:JAVA = 'C:\path\java.exe'; $env:GRAPHVIZ_DOT = 'C:\path\dot.exe'
# *_slide.puml files are Graphviz (@startdot) layouts with pinned positions: they are rendered with neato
# directly, because PlantUML passes "Times New Roman" to Pango as a style and writes its warnings into the PNG.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = Resolve-Path "$here\.."
$java = if ($env:JAVA) { $env:JAVA } else { 'java' }
$files = Get-ChildItem "$here\fig4_*.puml" | Where-Object { $_.Name -notlike '*_slide.puml' } | ForEach-Object { $_.FullName }
& $java -jar $env:PLANTUML_JAR -charset UTF-8 -tpng -o $out $files

$neato = if ($env:GRAPHVIZ_DOT) { Join-Path (Split-Path $env:GRAPHVIZ_DOT) 'neato.exe' } else { 'neato' }
foreach ($f in Get-ChildItem "$here\fig4_*_slide.puml") {
  $lines = Get-Content $f.FullName -Encoding UTF8
  $body = $lines | Where-Object { $_ -notmatch '^\s*(@startdot|@enddot|'')' }
  $dot = Join-Path $env:TEMP ($f.BaseName + '.dot')
  [IO.File]::WriteAllLines($dot, $body, (New-Object Text.UTF8Encoding $false))
  & $neato -Tpng $dot -o (Join-Path $out ($f.BaseName + '.png'))
}
