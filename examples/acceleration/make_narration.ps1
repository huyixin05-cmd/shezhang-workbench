$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$lessonRoot = $PSScriptRoot
$lessonAudio = Join-Path $lessonRoot 'render-local/audio'
New-Item -ItemType Directory -Path $lessonAudio -Force | Out-Null
$lessonSegments = Get-Content -LiteralPath (Join-Path $lessonRoot 'narration.json') -Raw -Encoding utf8 | ConvertFrom-Json
$lessonVoice = New-Object System.Speech.Synthesis.SpeechSynthesizer
$lessonVoice.SelectVoice('Microsoft Huihui Desktop')
$lessonVoice.Rate = 1
foreach ($segment in $lessonSegments) {
    $lessonVoice.SetOutputToWaveFile((Join-Path $lessonAudio ($segment.id + '.wav')))
    $lessonVoice.Speak($segment.text)
    $lessonVoice.SetOutputToNull()
}
$lessonVoice.Dispose()
