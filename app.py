import os
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import time
import numpy as np

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

def vhs_glitch_effect(img, warp_intensity=5, color_shift=2, scanline_intensity=0.5, noise_amount=0.3):
    """Apply VHS-style glitch effects"""
    from PIL import ImageDraw
    
    # Convert to numpy array for processing
    arr = np.array(img)
    
    # 1. Color shift (RGB channel offset)
    shifted = np.zeros_like(arr)
    shift_amount = color_shift
    shifted[:, shift_amount:] = arr[:, :-shift_amount]  # Red channel
    shifted[:, :shift_amount] = arr[:, -shift_amount:]  # Wrap around
    
    # 2. Warp effect (horizontal distortion)
    if warp_intensity > 0:
        height, width = arr.shape[:2]
        for y in range(height):
            offset = int(warp_intensity * np.sin(y / 20))
            shifted[y] = np.roll(shifted[y], offset, axis=0)
    
    # 3. Scanlines
    if scanline_intensity > 0:
        overlay = Image.new('L', img.size, 255)
        draw = ImageDraw.Draw(overlay)
        for y in range(0, img.size[1], 2):
            draw.line([(0, y), (img.size[0], y)], fill=int(255 * (1 - scanline_intensity)))
        arr = np.minimum(shifted, np.array(overlay)[..., np.newaxis])
    else:
        arr = shifted
    
    # 4. Noise
    if noise_amount > 0:
        noise = np.random.randint(0, int(255 * noise_amount), arr.shape[:2])
        noise = np.dstack([noise]*3)  # Convert to RGB
        arr = np.where(noise < (255 * noise_amount / 2), arr - noise, arr + noise)
        arr = np.clip(arr, 0, 255)
    
    return Image.fromarray(arr.astype('uint8'))

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
        with Image.open(os.path.join(UPLOAD_FOLDER, filename)) as img:
            # Process all active effects
            for effect in effects:
                if effect['name'] == 'pixelate':
                    img = pixelate_image(
                        img,
                        pixel_size=effect['params'].get('pixel_size', 10),
                        palette_size=effect['params'].get('palette_size', 16),
                        dither=effect['params'].get('dither', True)
                    )
                elif effect['name'] == 'vhs':
                    img = vhs_glitch_effect(
                        img,
                        warp_intensity=effect['params'].get('warp_intensity', 5),
                        color_shift=effect['params'].get('color_shift', 2),
                        scanline_intensity=effect['params'].get('scanline_intensity', 0.5),
                        noise_amount=effect['params'].get('noise_amount', 0.3)
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