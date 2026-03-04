from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import os
from werkzeug.utils import secure_filename
import uuid

def allowed_file(filename, allowed_extensions=None):
    """Check if file has allowed extension"""
    if allowed_extensions is None:
        from config import Config
        allowed_extensions = Config.ALLOWED_EXTENSIONS
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_unique_filename(original_filename):
    """Generate unique filename to prevent collisions"""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    return unique_name

def save_uploaded_file(file, upload_folder):
    """Save uploaded file with unique name"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = generate_unique_filename(filename)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        return file_path, unique_filename
    return None, None

def enhance_image_for_ai(image_path):
    """Enhance image for better AI prediction"""
    try:
        img = Image.open(image_path)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        
        # Apply slight denoising
        img = img.filter(ImageFilter.MedianFilter(size=3))
        
        # Save enhanced image
        img.save(image_path)
        
        return True
    except Exception as e:
        print(f"Error enhancing image: {e}")
        return False

def validate_image_size(image_path, max_size_mb=10):
    """Validate image file size"""
    file_size = os.path.getsize(image_path) / (1024 * 1024)  # Convert to MB
    return file_size <= max_size_mb