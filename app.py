import os
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import time

app = Flask(__name__)

# Config
UPLOAD_FOLDER = 'static/uploads'
PROCESSED_FOLDER = 'static/processed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def pixelate_image(img, pixel_size=10, palette_size=16, dither=True):
    """Apply pixelation effect with color reduction"""
    # Pixelate
    small_size = (max(1, img.width // pixel_size)), max(1, img.height // pixel_size)
    img_small = img.resize(small_size, Image.NEAREST)
    result = img_small.resize(img.size, Image.NEAREST)
    
    # Color reduction
    if palette_size < 256:
        dither_method = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE
        result = result.quantize(colors=palette_size, dither=dither_method)
    
    return result.convert('RGB')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = f"{int(time.time())}_{secure_filename(file.filename)}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        return jsonify({'filename': filename})
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    filename = data.get('filename')
    effects = data.get('effects', [])
    
    if not filename:
        return jsonify({'error': 'Filename missing'}), 400
    
    try:
        # Validate file exists
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Open image with explicit close
        with Image.open(filepath) as img:
            # Process effects
            pixelate_effect = next((e for e in effects if e['name'] == 'pixelate'), None)
            if pixelate_effect:
                img = pixelate_image(
                    img,
                    pixel_size=pixelate_effect['params'].get('pixel_size', 10),
                    palette_size=pixelate_effect['params'].get('palette_size', 16),
                    dither=pixelate_effect['params'].get('dither', True)
                )
            
            # Save processed image
            output_filename = f"processed_{int(time.time())}_{filename}"
            output_path = os.path.join(PROCESSED_FOLDER, output_filename)
            img.save(output_path)
            
            return jsonify({
                'processed_url': f"/static/processed/{output_filename}",
                'filename': output_filename
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)