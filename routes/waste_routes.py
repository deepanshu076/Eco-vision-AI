from flask import Blueprint, request, jsonify, render_template, session, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from database.waste_model import WasteUpload
from database.user_model import User
from database.db import db
from models.predict import classifier
from utils.image_hash import is_duplicate_image, calculate_perceptual_hash, get_all_image_hashes
from utils.image_preprocessing import save_uploaded_file, enhance_image_for_ai, validate_image_size
from utils.carbon_calculator import CarbonCalculator
from routes.auth_routes import login_required
import uuid

waste_bp = Blueprint('waste', __name__)
carbon_calculator = CarbonCalculator()

@waste_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Handle waste image upload and classification"""
    if request.method == 'GET':
        return render_template('upload.html')
    
    # Check if file was uploaded
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    # Save uploaded file
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path, filename = save_uploaded_file(file, upload_folder)
    
    if not file_path:
        flash('Invalid file type. Please upload an image.', 'error')
        return redirect(request.url)
    
    # Validate file size
    if not validate_image_size(file_path):
        os.remove(file_path)
        flash('File too large. Maximum size is 10MB.', 'error')
        return redirect(request.url)
    
    # Check for duplicates
    existing_hashes = get_all_image_hashes()
    is_duplicate, new_hash = is_duplicate_image(file_path, existing_hashes)
    
    if is_duplicate:
        os.remove(file_path)
        flash('This image has already been uploaded.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    # Enhance image for better prediction
    enhance_image_for_ai(file_path)
    
    # Make prediction
    try:
        prediction = classifier.predict(file_path)
        
        if not prediction['success']:
            os.remove(file_path)
            flash('Error analyzing image. Please try again.', 'error')
            return redirect(request.url)
        
        # Calculate carbon savings
        carbon_saved = carbon_calculator.calculate_savings(prediction['category'])['co2_saved']
        
        # Save to database
        waste_upload = WasteUpload(
            user_id=session['user_id'],
            image_path=filename,
            image_hash=new_hash,
            category=prediction['category'],
            confidence=prediction['confidence'],
            carbon_saved=carbon_saved
        )
        
        db.session.add(waste_upload)
        db.session.commit()
        
        # Get equivalents for display
        equivalents = carbon_calculator.get_equivalents(carbon_saved)
        
        return render_template('result.html',
                             prediction=prediction,
                             carbon_saved=carbon_saved,
                             equivalents=equivalents,
                             filename=filename)
    
    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        
        flash(f'Error processing image: {str(e)}', 'error')
        return redirect(request.url)

@waste_bp.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    """API endpoint for waste image upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save file
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path, filename = save_uploaded_file(file, upload_folder)
    
    if not file_path:
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Check for duplicates
    existing_hashes = get_all_image_hashes()
    is_duplicate, new_hash = is_duplicate_image(file_path, existing_hashes)
    
    if is_duplicate:
        os.remove(file_path)
        return jsonify({'error': 'Duplicate image'}), 409
    
    # Make prediction
    try:
        prediction = classifier.predict(file_path)
        
        if not prediction['success']:
            os.remove(file_path)
            return jsonify({'error': 'Prediction failed'}), 500
        
        # Calculate carbon savings
        carbon_saved = carbon_calculator.calculate_savings(prediction['category'])['co2_saved']
        
        # Save to database
        waste_upload = WasteUpload(
            user_id=session['user_id'],
            image_path=filename,
            image_hash=new_hash,
            category=prediction['category'],
            confidence=prediction['confidence'],
            carbon_saved=carbon_saved
        )
        
        db.session.add(waste_upload)
        db.session.commit()
        
        # Get equivalents
        equivalents = carbon_calculator.get_equivalents(carbon_saved)
        
        return jsonify({
            'success': True,
            'prediction': prediction,
            'carbon_saved': carbon_saved,
            'equivalents': equivalents,
            'upload_id': waste_upload.id
        }), 200
    
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500

@waste_bp.route('/history')
@login_required
def history():
    """View user's upload history"""
    user = User.query.get(session['user_id'])
    uploads = WasteUpload.query.filter_by(user_id=user.id)\
                               .order_by(WasteUpload.upload_date.desc())\
                               .all()
    
    return render_template('history.html', uploads=uploads)

@waste_bp.route('/api/history')
@login_required
def api_history():
    """API endpoint for upload history"""
    user = User.query.get(session['user_id'])
    uploads = WasteUpload.query.filter_by(user_id=user.id)\
                               .order_by(WasteUpload.upload_date.desc())\
                               .all()
    
    return jsonify({
        'uploads': [u.to_dict() for u in uploads]
    })