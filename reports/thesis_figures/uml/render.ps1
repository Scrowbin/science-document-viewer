# Renders every fig4_*.puml in this folder to PNG next to the thesis figures (reports/thesis_figures/).
# Needs Java and PlantUML; Graphviz for use case, class, component and deployment diagrams.
#   $env:PLANTUML_JAR = 'C:\path\plantuml.jar'; $env:JAVA = 'C:\path\java.exe'; $env:GRAPHVIZ_DOT = 'C:\path\dot.exe'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$java = if ($env:JAVA) { $env:JAVA } else { 'java' }
& $java -jar $env:PLANTUML_JAR -charset UTF-8 -tpng -o (Resolve-Path "$here\..") "$here\fig4_*.puml"
