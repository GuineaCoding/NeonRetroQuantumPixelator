document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');
    const canvas = document.getElementById('preview-canvas');
    const ctx = canvas.getContext('2d');
    const effectParams = document.getElementById('effect-params');
    const effectStack = document.getElementById('effect-stack');
    const exportBtn = document.getElementById('export-btn');

    let currentImage = null;
    let activeEffects = [];

    // Handle file selection
    fileInput.addEventListener('change', handleFileUpload);
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.border = '3px dashed #0f0';
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.border = '3px dashed #f0f';
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.border = '3px dashed #f0f';
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileUpload();
        }
    });

    // Effect buttons
    document.querySelectorAll('.effect-library button').forEach(button => {
        button.addEventListener('click', () => {
            const effectName = button.dataset.effect;
            addEffect(effectName);
        });
    });

    // Export button
    exportBtn.addEventListener('click', exportImage);

    // Functions
    async function handleFileUpload() {
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('image', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.error) {
                alert(data.error);
                return;
            }

            const img = new Image();
            img.src = `/static/uploads/${data.filename}`;
            img.onload = () => {
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
                canvas.style.display = 'block';
                dropZone.style.display = 'none';
                currentImage = data.filename;
            };
        } catch (error) {
            alert('Upload failed: ' + error.message);
        }
    }

    function addEffect(effectName) {
        if (!currentImage) {
            alert('Upload an image first!');
            return;
        }

        if (activeEffects.some(e => e.name === effectName)) {
            alert('Effect already applied!');
            return;
        }

        // Add to active effects
        const effect = {
            name: effectName,
            params: {}
        };
        activeEffects.push(effect);
        updateEffectStack();
        updateEffectControls(effectName);
        processEffects();
    }

    function updateEffectStack() {
        effectStack.innerHTML = '';
        activeEffects.forEach((effect, index) => {
            const effectElement = document.createElement('div');
            effectElement.className = 'active-effect';
            effectElement.innerHTML = `
                <span>${effect.name.toUpperCase()}</span>
                <button class="remove-effect" data-index="${index}">×</button>
            `;
            effectStack.appendChild(effectElement);
        });

        // Add remove event listeners
        document.querySelectorAll('.remove-effect').forEach(button => {
            button.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index);
                activeEffects.splice(index, 1);
                updateEffectStack();
                processEffects();
            });
        });
    }

function updateEffectControls(effectName) {
    let html = '';
    
    if (effectName === 'pixelate') {
        html = `
            <div class="control-group">
                <h4>PIXELATE</h4>
                <label>PIXEL SIZE: <span id="pixel-size-value">10</span>
                    <input type="range" id="pixel-size" min="5" max="50" value="10">
                </label>
                <label>COLORS: <span id="palette-size-value">16</span>
                    <input type="range" id="palette-size" min="2" max="32" value="16">
                </label>
                <label>
                    <input type="checkbox" id="dither" checked> DITHERING
                </label>
            </div>
        `;
    }
    // Add other effect controls here...
    
    effectParams.innerHTML = html;
    
    // Add event listeners for pixelate controls
    if (effectName === 'pixelate') {
        const pixelSizeSlider = document.getElementById('pixel-size');
        const paletteSizeSlider = document.getElementById('palette-size');
        const ditherCheckbox = document.getElementById('dither');
        
        const updatePixelEffect = () => {
            const effect = activeEffects.find(e => e.name === 'pixelate');
            if (effect) {
                effect.params = {
                    size: parseInt(pixelSizeSlider.value),
                    palette_size: parseInt(paletteSizeSlider.value),
                    dither: ditherCheckbox.checked
                };
                processEffects();
            }
        };
        
        pixelSizeSlider.addEventListener('input', (e) => {
            document.getElementById('pixel-size-value').textContent = e.target.value;
            updatePixelEffect();
        });
        
        paletteSizeSlider.addEventListener('input', (e) => {
            document.getElementById('palette-size-value').textContent = e.target.value;
            updatePixelEffect();
        });
        
        ditherCheckbox.addEventListener('change', updatePixelEffect);
    }
}

    async function processEffects() {
        if (!currentImage || activeEffects.length === 0) return;

        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: currentImage,
                    effects: activeEffects
                })
            });
            const data = await response.json();

            if (data.error) {
                alert(data.error);
                return;
            }

            // Update preview
            const img = new Image();
            img.src = data.processed_url;
            img.onload = () => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);
            };
        } catch (error) {
            alert('Processing failed: ' + error.message);
        }
    }

    function exportImage() {
        if (!currentImage) {
            alert('No image to export!');
            return;
        }
        alert('Export functionality would save the processed image');
    }
});