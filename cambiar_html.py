import os
import urllib.request

base_dir = r"C:\Users\20233280187\Desktop\local-pdf-tools"
html_path = os.path.join(base_dir, "app", "static", "index.html")

# Leer el HTML que ya tenés
with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# Verificar si tiene el logo SVG grande
if 'viewBox="0 0 1000 300"' in content:
    print("✅ El HTML YA TIENE el logo grande de v0.1.0")
    print("El problema NO es el HTML, debe ser otra cosa")
else:
    print("❌ El HTML NO tiene el logo grande")
    print("Necesitamos reinstalarlo")