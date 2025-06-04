import os
from flask import Flask, request, render_template, url_for
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)

# Configure folders
UPLOAD_FOLDER = 'static/uploads'
PIXELATED_FOLDER = 'static/pixelated'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PIXELATED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def pixelate(image_path, pixel_size=20):
    img = Image.open(image_path)

    # Shrink and expand image to create pixelation
    small_size = (max(1, img.width // pixel_size), max(1, img.height // pixel_size))
    img_small = img.resize(small_size, resample=Image.NEAREST)
    result = img_small.resize(img.size, Image.NEAREST)

    # Save to pixelated folder
    filename = os.path.basename(image_path)
    pixelated_path = os.path.join(PIXELATED_FOLDER, filename)
    result.save(pixelated_path)
    return pixelated_path

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'image' not in request.files:
            return "No file part", 400

        file = request.files['image']

        if file.filename == '':
            return "No selected file", 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            # Apply pixelation
            pixelated_path = pixelate(filepath)
            pixelated_filename = os.path.basename(pixelated_path)

            return render_template('index.html',
                                   filename=filename,
                                   pixelated_filename=pixelated_filename)
        else:
            return "Invalid file type", 400

    return render_template('index.html')
if __name__ == '__main__':
    app.run(debug=True)