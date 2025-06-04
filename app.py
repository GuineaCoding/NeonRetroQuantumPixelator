import os
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image, ImageFilter, ImageOps
import numpy as np
import time

app = Flask(__name__)

# Config
UPLOAD_FOLDER = 'static/uploads'
PROCESSED_FOLDER = 'static/processed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
EFFECTS = {
    'pixelate': {'size': 10},
    'crt_scanlines': {'opacity': 50},
    '8bit': {'palette_size': 16},
    'vhs': {'glitch_intensity': 30}
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def apply_effect(img, effect_name, params):
    if effect_name == 'pixelate':
        # Enhanced pixelation with all controls
        pixel_size = params.get('size', 10)
        palette_size = params.get('palette_size', 16)
        dither = params.get('dither', False)
        
        # Pixelate
        small_size = (max(1, img.width // pixel_size), max(1, img.height // pixel_size))
        img_small = img.resize(small_size, Image.NEAREST)
        result = img_small.resize(img.size, Image.NEAREST)
        
        # Color reduction
        if palette_size < 256:
            dither_method = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE
            result = result.quantize(colors=palette_size, dither=dither_method)
        
        return result.convert('RGB')
    
    elif effect_name == 'crt_scanlines':
        opacity = params.get('opacity', 50) / 100
        scanline = Image.new('L', (2, 2), 255)
        scanline.putpixel((0, 1), int(255 * (1 - opacity)))
        scanline = scanline.resize(img.size, Image.NEAREST)
        return Image.composite(img, Image.new('RGB', img.size, 'black'), scanline)
    
    elif effect_name == '8bit':
        palette_size = params.get('palette_size', 16)
        return img.quantize(colors=palette_size).convert('RGB')
    
    elif effect_name == 'vhs':
        # Simulate VHS glitch by shifting RGB channels
        arr = np.array(img)
        r = np.roll(arr[:, :, 0], params.get('glitch_intensity', 5), axis=1)
        g = np.roll(arr[:, :, 1], -params.get('glitch_intensity', 3), axis=1)
        return Image.fromarray(np.stack([r, g, arr[:, :, 2]], axis=-1))
    
    return img

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', effects=EFFECTS)

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
        img = Image.open(os.path.join(UPLOAD_FOLDER, filename))
        
        for effect in effects:
            img = apply_effect(img, effect['name'], effect['params'])
        
        output_filename = f"processed_{filename}"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        img.save(output_path)
        
        return jsonify({'processed_url': f"/static/processed/{output_filename}"})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)