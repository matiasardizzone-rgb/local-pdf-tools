import os
import sys
import time
import threading
import socket
from waitress import serve
import webview
class Api:
    def saveFileDialog(self, default_name):
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        file_path = filedialog.asksaveasfilename(defaultextension='.pdf', initialfile=default_name, filetypes=[('PDF files', '*.pdf'), ('All files', '*.*')])
        root.destroy()
        return file_path if file_path else None
    
    def saveFile(self, src_path, dest_path):
        import shutil
        shutil.copyfile(src_path, dest_path)
        return True



# Importar la app de Flask
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import app

def buscar_puerto_libre():
    """Busca un puerto TCP libre dinámicamente."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

if __name__ == '__main__':
    print("Iniciando Local PDF Tools...")
    puerto = buscar_puerto_libre()
    
    # Iniciar el servidor Flask en un thread separado
    def iniciar_servidor():
        serve(app, host='127.0.0.1', port=puerto, threads=4)
    
    thread_servidor = threading.Thread(target=iniciar_servidor, daemon=True)
    thread_servidor.start()
    
    print(f"Servidor corriendo en: http://localhost:{puerto}")
    print("Cerra la ventana para salir de la aplicacion.\n")
    
    # Crear la ventana nativa con PyWebView
    url = f"http://localhost:{puerto}"
    window = webview.create_window(
        'Local PDF Tools',
        url,
        js_api=Api(),
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        fullscreen=False
    )
    
    # Iniciar PyWebView (esto bloquea hasta que se cierre la ventana)
    webview.start()
    
    print("\nLocal PDF Tools cerrado.")
    sys.exit(0)
