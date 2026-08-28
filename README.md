# Local PDF Tools

Herramientas PDF 100% locales. Tus documentos nunca salen de tu máquina.

## Características

- **Unir PDFs**: Combina múltiples PDFs en uno solo
- **Comprimir PDF**: Reduce el tamaño con 3 niveles (Baja, Media, Alta)
- **PDF a Word**: Convierte PDFs a documentos Word editables
- **Office a PDF**: Convierte Word/Excel a PDF
- **OCR**: Extrae texto de PDFs escaneados o aplica capa de texto invisible
- **Extraer páginas**: Selecciona páginas específicas de un PDF
- **Dividir PDF**: Separa un PDF en múltiples archivos
- **Rotar páginas**: Rota páginas individuales o todo el documento

## Requisitos

- Python 3.8+
- Tesseract OCR (para funciones de OCR)
- Poppler (para funciones de OCR)
- Microsoft Word o LibreOffice (para Office a PDF)

## Instalación

1. Clonar el repositorio
2. Instalar dependencias: `pip install -r requirements.txt`
3. Ejecutar: `python app/launcher.py`

## Tecnologías

- Python + Flask
- PyWebView (ventana nativa)
- PyMuPDF (manipulación de PDFs)
- Tesseract OCR (reconocimiento de texto)

## Autor

Matias Ardizzone