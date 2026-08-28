import os
import base64
import sys
import socket
import time
import threading
import warnings
import subprocess
from flask import Flask, request, jsonify, send_file
from waitress import serve
from werkzeug.utils import secure_filename

warnings.filterwarnings("ignore", message="The fitz API is deprecated")

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'app')
    else:
        return os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
base_path = get_base_path()
static_path = os.path.join(base_path, 'static')
app.static_folder = static_path
app.static_url_path = '/static'

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def find_tesseract():
    paths = [r"C:\Program Files\Tesseract-OCR\tesseract.exe", r"C:\Archivos de programa\Tesseract-OCR\tesseract.exe"]
    return next((p for p in paths if os.path.exists(p)), None)

def find_poppler():
    paths = [r"C:\Program Files\poppler\Library\bin", r"C:\Archivos de programa\poppler\Library\bin"]
    return next((p for p in paths if os.path.exists(p)), None)

@app.route('/')
def index():
    return send_file(os.path.join(app.static_folder, 'index.html'))

@app.route('/api/merge', methods=['POST'])
def merge_pdfs():
    if 'files' not in request.files:
        return jsonify({'error': 'No se enviaron archivos'}), 400
    files = request.files.getlist('files')
    valid_files = [f for f in files if f.filename != '']
    if len(valid_files) < 2:
        return jsonify({'error': 'Se necesitan al menos 2 archivos PDF'}), 400
    try:
        import pymupdf
        merged = pymupdf.open()
        for file in valid_files:
            filename = secure_filename(file.filename)
            pdf_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(pdf_path)
            doc = pymupdf.open(pdf_path)
            merged.insert_pdf(doc)
            doc.close()
            os.remove(pdf_path)
        base_name = "unido_" + str(int(time.time()))
        output_pdf = os.path.join(UPLOAD_FOLDER, base_name + ".pdf")
        merged.save(output_pdf)
        merged.close()
        return jsonify({'file_path': output_pdf, 'filename': base_name + ".pdf"})
    except Exception as e:
        return jsonify({'error': f'Error al unir: {str(e)}'}), 500

@app.route('/api/compress', methods=['POST'])
def compress_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No se envio ningun archivo'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'El archivo no tiene nombre'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Solo se permiten archivos PDF'}), 400
    try:
        import pymupdf
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(pdf_path)
        base_name = os.path.splitext(filename)[0]
        compressed_filename = f"{base_name}_comprimido.pdf"
        compressed_path = os.path.join(UPLOAD_FOLDER, compressed_filename)
        doc = pymupdf.open(pdf_path)
        level = request.form.get('level', 'media')
        if level == 'baja':
            doc.save(compressed_path, garbage=1, deflate=False)
        elif level == 'alta':
            doc.save(compressed_path, garbage=4, deflate=True, clean=True, compress_images=True)
        else:
            doc.save(compressed_path, garbage=3, deflate=True, clean=True)
        doc.close()
        return jsonify({'file_path': compressed_path, 'filename': compressed_filename})
    except Exception as e:
        return jsonify({'error': f'Error al comprimir: {str(e)}'}), 500

@app.route('/api/pdf-to-word', methods=['POST'])
def pdf_to_word():
    if 'file' not in request.files:
        return jsonify({'error': 'No se envio ningun archivo'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'El archivo no tiene nombre'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Solo se permiten archivos PDF'}), 400
    try:
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(pdf_path)
        docx_filename = os.path.splitext(filename)[0] + '.docx'
        docx_path = os.path.join(UPLOAD_FOLDER, docx_filename)
        from pdf2docx import Converter
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
        return jsonify({'file_path': docx_path, 'filename': docx_filename})
    except Exception as e:
        return jsonify({'error': f'Error al convertir: {str(e)}'}), 500

@app.route('/api/office-to-pdf', methods=['POST'])
def office_to_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No se envio ningun archivo'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'El archivo no tiene nombre'}), 400
    ext = file.filename.lower().split('.')[-1]
    if ext not in ['docx', 'doc', 'xlsx', 'xls']:
        return jsonify({'error': 'Solo se permiten archivos de Word o Excel'}), 400
    try:
        filename = secure_filename(file.filename)
        office_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(office_path)
        base_name = os.path.splitext(filename)[0]
        pdf_filename = f"{base_name}.pdf"
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
        try:
            from docx2pdf import convert
            if ext in ['docx', 'doc']:
                convert(office_path, pdf_path)
                if os.path.exists(pdf_path):
                    return jsonify({'file_path': pdf_path, 'filename': pdf_filename})
        except Exception: pass
        try:
            cmd = ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', UPLOAD_FOLDER, office_path]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            generated_pdf = os.path.join(UPLOAD_FOLDER, f"{base_name}.pdf")
            if os.path.exists(generated_pdf):
                return jsonify({'file_path': generated_pdf, 'filename': pdf_filename})
        except Exception: pass
        return jsonify({'error': 'REQUIERE_LIBREOFFICE', 'message': 'Necesitas tener instalado Microsoft Word o LibreOffice.'}), 400
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/ocr', methods=['POST'])
def ocr_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No se envio ningun archivo'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'El archivo no tiene nombre'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Solo se permiten archivos PDF'}), 400
    try:
        import pytesseract
        from pdf2image import convert_from_path
        tesseract_path = find_tesseract()
        if not tesseract_path:
            return jsonify({'error': 'REQUIERE_TESSERACT', 'message': 'No se encontro Tesseract OCR instalado.'}), 400
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        poppler_bin = find_poppler()
        if not poppler_bin:
            return jsonify({'error': 'REQUIERE_POPPLER', 'message': 'No se encontro Poppler instalado.'}), 400
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(pdf_path)
        base_name = os.path.splitext(filename)[0]
        txt_filename = f"{base_name}_ocr.txt"
        txt_path = os.path.join(UPLOAD_FOLDER, txt_filename)
        pages = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_bin)
        text = ""
        for i, page in enumerate(pages):
            page_text = pytesseract.image_to_string(page, lang='spa+eng')
            text += f"\n--- Pagina {i+1} ---\n{page_text}\n"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return send_file(txt_path, as_attachment=True, download_name=txt_filename, mimetype='text/plain')
    except Exception as e:
        return jsonify({'error': f'Error en OCR: {str(e)}'}), 500

@app.route('/api/ocr-to-pdf', methods=['POST'])
def ocr_to_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No se envio ningun archivo'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'El archivo no tiene nombre'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Solo se permiten archivos PDF'}), 400
    try:
        import pymupdf
        tesseract_path = find_tesseract()
        if not tesseract_path:
            return jsonify({'error': 'REQUIERE_TESSERACT', 'message': 'No se encontro Tesseract OCR instalado.'}), 400
        tessdata = os.path.join(os.path.dirname(tesseract_path), 'tessdata')
        langs = [l for l in ['spa', 'eng'] if os.path.exists(os.path.join(tessdata, l + '.traineddata'))]
        lang_arg = '+'.join(langs) if langs else 'eng'
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(pdf_path)
        base_name = os.path.splitext(filename)[0]
        doc = pymupdf.open(pdf_path)
        zoom = 300 / 72.0
        mat = pymupdf.Matrix(zoom, zoom)
        page_pdfs = []
        pngs = []
        for n, page in enumerate(doc):
            pix = page.get_pixmap(matrix=mat)
            img_path = os.path.join(UPLOAD_FOLDER, base_name + '_p' + str(n) + '.png')
            pix.save(img_path)
            pngs.append(img_path)
            out_base = os.path.join(UPLOAD_FOLDER, base_name + '_p' + str(n) + '_ocr')
            cmd = [tesseract_path, img_path, out_base, '-l', lang_arg, 'pdf']
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                doc.close()
                return jsonify({'error': 'Tesseract fallo: ' + (r.stderr or r.stdout)[-400:]}), 500
            page_pdfs.append(out_base + '.pdf')
        doc.close()
        merged = pymupdf.open()
        for p in page_pdfs:
            d = pymupdf.open(p)
            merged.insert_pdf(d)
            d.close()
        output_pdf = os.path.join(UPLOAD_FOLDER, base_name + '_ocr.pdf')
        merged.save(output_pdf)
        merged.close()
        for p in page_pdfs + pngs:
            try: os.remove(p)
            except Exception: pass
        return jsonify({'pdf_path': output_pdf, 'filename': base_name + '_ocr.pdf'})
    except Exception as e:
        return jsonify({'error': f'Error en OCR a PDF: {str(e)}'}), 500


@app.route('/api/get-thumbnails', methods=['POST'])
def get_thumbnails():
    if 'file' not in request.files:
        return jsonify({'error': 'No se envio ningun archivo'}), 400
    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Solo se permiten archivos PDF'}), 400
    try:
        import pymupdf
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(pdf_path)
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        thumbnails = []
        for i in range(total_pages):
            page = doc[i]
            mat = pymupdf.Matrix(0.3, 0.3)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            thumbnails.append({
                'page': i + 1,
                'image': f"data:image/png;base64,{img_base64}"
            })
        doc.close()
        return jsonify({'total': total_pages, 'thumbnails': thumbnails})
    except Exception as e:
        return jsonify({'error': f'Error al generar miniaturas: {str(e)}'}), 500


@app.route('/api/split-pdf', methods=['POST'])
def split_pdf():
    import zipfile
    import io
    import json
    if 'file' not in request.files:
        return jsonify({'error': 'No se envio ningun archivo'}), 400
    file = request.files['file']
    groups_json = request.form.get('groups', '{}')
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Solo se permiten archivos PDF'}), 400
    try:
        groups = json.loads(groups_json)
        if not groups:
            return jsonify({'error': 'No se definieron grupos'}), 400
        import pymupdf
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(pdf_path)
        doc = pymupdf.open(pdf_path)
        base_name = os.path.splitext(filename)[0]
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for group_name, pages in groups.items():
                if not pages:
                    continue
                new_doc = pymupdf.open()
                for p in sorted(pages):
                    if 0 <= p < len(doc):
                        new_doc.insert_pdf(doc, from_page=p, to_page=p)
                part_filename = f"{base_name}_{group_name}.pdf"
                part_buffer = io.BytesIO()
                new_doc.save(part_buffer)
                new_doc.close()
                zf.writestr(part_filename, part_buffer.getvalue())
        doc.close()
        zip_buffer.seek(0)
        zip_path = os.path.join(UPLOAD_FOLDER, base_name + "_dividido.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_buffer.getvalue())
        return jsonify({'file_path': zip_path, 'filename': base_name + "_dividido.zip"})
    except Exception as e:
        return jsonify({'error': f'Error al dividir: {str(e)}'}), 500


@app.route('/api/rotate-pdf', methods=['POST'])
def rotate_pdf():
    import json
    if 'file' not in request.files:
        return jsonify({'error': 'No se envio ningun archivo'}), 400
    file = request.files['file']
    rotations_json = request.form.get('rotations', '{}')
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Solo se permiten archivos PDF'}), 400
    try:
        rotations = json.loads(rotations_json)
        import pymupdf
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(pdf_path)
        doc = pymupdf.open(pdf_path)
        for page_idx, angle in rotations.items():
            page_idx = int(page_idx)
            angle = int(angle)
            if 0 <= page_idx < len(doc) and angle != 0:
                doc[page_idx].set_rotation(angle)
        base_name = os.path.splitext(filename)[0]
        output_pdf = os.path.join(UPLOAD_FOLDER, base_name + "_rotado.pdf")
        doc.save(output_pdf)
        doc.close()
        return jsonify({'file_path': output_pdf, 'filename': base_name + "_rotado.pdf"})
    except Exception as e:
        return jsonify({'error': f'Error al rotar: {str(e)}'}), 500

@app.route('/api/extract-pages', methods=['POST'])
def extract_pages():
    if 'file' not in request.files:
        return jsonify({'error': 'No se envio ningun archivo'}), 400
    file = request.files['file']
    pages_str = request.form.get('pages', '')
    if file.filename == '' or not pages_str:
        return jsonify({'error': 'Falta el archivo o el rango de paginas'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Solo se permiten archivos PDF'}), 400
    try:
        import pymupdf
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(pdf_path)
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        new_doc = pymupdf.open()
        pages_to_extract = []
        for part in pages_str.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages_to_extract.extend(range(start - 1, end))
            else:
                pages_to_extract.append(int(part) - 1)
        pages_to_extract = sorted(list(set(p for p in pages_to_extract if 0 <= p < total_pages)))
        if not pages_to_extract:
            doc.close()
            return jsonify({'error': 'Rango de paginas invalido'}), 400
        for p in pages_to_extract:
            new_doc.insert_pdf(doc, from_page=p, to_page=p)
        base_name = os.path.splitext(filename)[0]
        output_pdf = os.path.join(UPLOAD_FOLDER, f"{base_name}_extraido.pdf")
        new_doc.save(output_pdf)
        new_doc.close()
        doc.close()
        return jsonify({'file_path': output_pdf, 'filename': f"{base_name}_extraido.pdf"})
    except Exception as e:
        return jsonify({'error': f'Error al extraer: {str(e)}'}), 500

@app.route('/api/save-txt', methods=['POST'])
def save_txt():
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    name = secure_filename(data.get('name', 'ocr.txt'))
    if not name.endswith('.txt'): name += '.txt'
    dest_dir = os.path.join(os.path.expanduser('~'), 'Documents')
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, name)
    with open(dest, 'w', encoding='utf-8') as f: f.write(text)
    return jsonify({'saved': dest})

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    print("\nCerrando Local PDF Tools...")
    os._exit(0)

def buscar_puerto_libre():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

if __name__ == '__main__':
    print("Iniciando Local PDF Tools...")
    puerto = buscar_puerto_libre()
    print(f"Servidor corriendo en: http://localhost:{puerto}")
    serve(app, host='127.0.0.1', port=puerto, threads=4)
