# peasy-audio — Audio Processing Library Demo
Output demo.gif

Set FontSize 20
Set Width 1000
Set Height 580
Set Shell "zsh"
Set Theme "Catppuccin Mocha"
Set TypingSpeed 30ms
Set Padding 24

Type "uv run --with peasy-audio python3"
Enter
Sleep 2.5s

Type "import peasy_audio"
Enter
Sleep 1s

Type "# Available audio operations"
Enter
Sleep 0.5s

Type "[f for f in dir(peasy_audio) if not f.startswith('_')]"
Enter
Sleep 2s

Type "# Supported audio formats"
Enter
Sleep 0.5s

Type "from peasy_audio import AudioFormat"
Enter
Sleep 0.5s

Type "list(AudioFormat.__args__)"
Enter
Sleep 2s

Type "# Functions: info, convert, trim, merge, normalize,"
Enter
Sleep 0.5s

Type "#   fade, speed, reverse_audio, change_volume, overlay"
Enter
Sleep 0.5s

Type "from peasy_audio import info, silence"
Enter
Sleep 0.5s

Type "# Generate 2 seconds of silence"
Enter
Sleep 0.5s

Type "result = silence(duration_ms=2000)"
Enter
Sleep 1.5s

Type "print(f'Generated {len(result.data):,} bytes of silence')"
Enter
Sleep 2s

Type "exit()"
Enter
Sleep 1s
