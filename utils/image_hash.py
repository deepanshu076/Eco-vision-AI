import imagehash
from PIL import Image
import hashlib
import os

def calculate_perceptual_hash(image_path, hash_size=8):
    """
    Calculate perceptual hash of an image
    This helps detect visually similar images even if slightly modified
    """
    try:
        img = Image.open(image_path)
        phash = imagehash.phash(img, hash_size=hash_size)
        return str(phash)
    except Exception as e:
        print(f"Error calculating perceptual hash: {e}")
        return None

def calculate_md5_hash(image_path):
    """Calculate MD5 hash of an image file"""
    hash_md5 = hashlib.md5()
    with open(image_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def is_duplicate_image(image_path, existing_hashes, threshold=5):
    """
    Check if image is duplicate using perceptual hash
    existing_hashes: list of existing perceptual hashes
    threshold: maximum Hamming distance to consider as duplicate
    """
    new_hash = calculate_perceptual_hash(image_path)
    if not new_hash:
        return False, None
    
    new_hash_obj = imagehash.hex_to_hash(new_hash)
    
    for existing_hash in existing_hashes:
        existing_hash_obj = imagehash.hex_to_hash(existing_hash)
        hamming_distance = new_hash_obj - existing_hash_obj
        
        if hamming_distance <= threshold:
            return True, existing_hash
    
    return False, new_hash

def get_all_image_hashes():
    """Get all existing image hashes from database"""
    from database.waste_model import WasteUpload
    from database.db import db
    
    hashes = WasteUpload.query.with_entities(WasteUpload.image_hash).all()
    return [h[0] for h in hashes]