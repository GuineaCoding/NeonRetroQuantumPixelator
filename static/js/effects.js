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

        // Add to active effects with default parameters
        const effect = {
            name: effectName,
            params: {}
        };
        
        if (effectName === 'pixelate') {
            effect.params = {
                pixel_size: 10,
                palette_size: 16,
                dither: true
            };
        } else if (effectName === 'vhs') {
            effect.params = {
                warp_intensity: 5,
                color_shift: 2,
                scanline_intensity: 0.5,
                noise_amount: 0.3
            };
        }

        activeEffects = [effect]; 
        updateEffectStack();
        updateEffectControls(effectName);
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
            const effect = activeEffects.find(e => e.name === 'pixelate');
            html = `
            <div class="control-group">
                <h4>PIXELATE</h4>
                <label>PIXEL SIZE: <span id="pixel-size-value">${effect.params.pixel_size}</span>
                    <input type="range" id="pixel-size" min="5" max="50" value="${effect.params.pixel_size}">
                </label>
                <label>COLORS: <span id="palette-size-value">${effect.params.palette_size}</span>
                    <input type="range" id="palette-size" min="2" max="32" value="${effect.params.palette_size}">
                </label>
                <label>
                    <input type="checkbox" id="dither" ${effect.params.dither ? 'checked' : ''}> DITHERING
                </label>
            </div>
        `;
        } else if (effectName === 'vhs') {
            const effect = activeEffects.find(e => e.name === 'vhs');
            html = `
            <div class="control-group">
                <h4>VHS GLITCH</h4>
                <label>WARP: <span id="vhs-warp-value">${effect.params.warp_intensity}</span>
                    <input type="range" id="vhs-warp" min="0" max="10" value="${effect.params.warp_intensity}">
                </label>
                <label>COLOR SHIFT: <span id="vhs-shift-value">${effect.params.color_shift}</span>
                    <input type="range" id="vhs-shift" min="0" max="5" value="${effect.params.color_shift}">
                </label>
                <label>SCANLINES: <span id="vhs-scanline-value">${Math.round(effect.params.scanline_intensity * 100)}%</span>
                    <input type="range" id="vhs-scanline" min="0" max="100" value="${effect.params.scanline_intensity * 100}">
                </label>
                <label>NOISE: <span id="vhs-noise-value">${Math.round(effect.params.noise_amount * 100)}%</span>
                    <input type="range" id="vhs-noise" min="0" max="100" value="${effect.params.noise_amount * 100}">
                </label>
            </div>
        `;
        } else {
            applyBtn.style.display = 'none';
        }

        effectParams.innerHTML = html;
        applyBtn.style.display = 'block';

    
        if (effectName === 'pixelate') {
            // ... existing pixelate event listeners ...
        } else if (effectName === 'vhs') {
            const warpSlider = document.getElementById('vhs-warp');
            const shiftSlider = document.getElementById('vhs-shift');
            const scanlineSlider = document.getElementById('vhs-scanline');
            const noiseSlider = document.getElementById('vhs-noise');

            const updateVHSEffect = () => {
                const effect = activeEffects.find(e => e.name === 'vhs');
                if (effect) {
                    effect.params = {
                        warp_intensity: parseInt(warpSlider.value),
                        color_shift: parseInt(shiftSlider.value),
                        scanline_intensity: parseInt(scanlineSlider.value) / 100,
                        noise_amount: parseInt(noiseSlider.value) / 100
                    };
                    document.getElementById('vhs-warp-value').textContent = warpSlider.value;
                    document.getElementById('vhs-shift-value').textContent = shiftSlider.value;
                    document.getElementById('vhs-scanline-value').textContent = scanlineSlider.value + '%';
                    document.getElementById('vhs-noise-value').textContent = noiseSlider.value + '%';
                }
            };

            warpSlider.addEventListener('input', updateVHSEffect);
            shiftSlider.addEventListener('input', updateVHSEffect);
            scanlineSlider.addEventListener('input', updateVHSEffect);
            noiseSlider.addEventListener('input', updateVHSEffect);
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