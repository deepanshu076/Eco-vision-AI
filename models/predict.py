import tensorflow as tf
import numpy as np
from PIL import Image
import json
import os

class WasteClassifier:
    def __init__(self, model_path='models/mobilenet_model.h5'):
        self.model_path = model_path
        self.model = None
        self.class_indices = None
        self.img_size = (224, 224)
        self.load_model()
        
    def load_model(self):
        """Load the trained model and class indices"""
        if os.path.exists(self.model_path):
            self.model = tf.keras.models.load_model(self.model_path)
            print(f"Model loaded from {self.model_path}")
        else:
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        
        # Load class indices
        indices_path = 'models/class_indices.json'
        if os.path.exists(indices_path):
            with open(indices_path, 'r') as f:
                self.class_indices = json.load(f)
            # Reverse mapping
            self.classes = {v: k for k, v in self.class_indices.items()}
        else:
            # Default mapping
            self.classes = {0: 'biodegradable', 1: 'recyclable', 2: 'hazardous'}
    
    def preprocess_image(self, image_path):
        """Preprocess image for prediction"""
        # Load and resize image
        img = Image.open(image_path)
        img = img.convert('RGB')  # Ensure RGB
        img = img.resize(self.img_size)
        
        # Convert to array and normalize
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    
    def predict(self, image_path):
        """Predict waste category for an image"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        # Preprocess image
        processed_img = self.preprocess_image(image_path)
        
        # Make prediction
        predictions = self.model.predict(processed_img, verbose=0)
        
        # Get class and confidence
        predicted_class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_class_idx])
        
        # Map to category
        predicted_category = self.classes[predicted_class_idx]
        
        # Get all class probabilities
        class_probabilities = {}
        for idx, prob in enumerate(predictions[0]):
            class_name = self.classes[idx]
            class_probabilities[class_name] = float(prob)
        
        return {
            'category': predicted_category,
            'confidence': confidence,
            'probabilities': class_probabilities,
            'success': True
        }
    
    def predict_batch(self, image_paths):
        """Predict for multiple images"""
        results = []
        for path in image_paths:
            try:
                result = self.predict(path)
                result['image_path'] = path
                results.append(result)
            except Exception as e:
                results.append({
                    'image_path': path,
                    'error': str(e),
                    'success': False
                })
        return results

# Singleton instance
classifier = WasteClassifier()