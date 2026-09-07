cd C:\Users\20233280187\Desktop\local-pdf-tools

# Crear un script temporal para modificar launcher.py
@"
import os

launcher_path = "app/launcher.py"
with open(launcher_path, "r", encoding="utf-8") as f:
    content = f.read()

# Agregar el parámetro icon si no existe
if "icon=" not in content:
    content = content.replace(
        "window = webview.create_window(",
        "window = webview.create_window(\n        icon='localpdf-logo.ico',"
    )
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Ícono agregado a launcher.py")
else:
    print("️  launcher.py ya tiene el parámetro icon")
"@ | Out-File -FilePath "add_icon.py" -Encoding UTF8

python add_icon.py