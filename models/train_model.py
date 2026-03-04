import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix

class WasteClassifierTrainer:
    def __init__(self, img_size=(224, 224), batch_size=32, num_classes=3):
        self.img_size = img_size
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.model = None
        
    def prepare_data(self, data_dir='data'):
        """Prepare data generators with augmentation"""
        # Data augmentation for training
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            horizontal_flip=True,
            fill_mode='nearest',
            validation_split=0.2
        )
        
        # Only rescaling for validation
        val_datagen = ImageDataGenerator(
            rescale=1./255,
            validation_split=0.2
        )
        
        # Load training data
        train_generator = train_datagen.flow_from_directory(
            data_dir,
            target_size=self.img_size,
            batch_size=self.batch_size,
            class_mode='categorical',
            subset='training',
            shuffle=True
        )
        
        # Load validation data
        validation_generator = val_datagen.flow_from_directory(
            data_dir,
            target_size=self.img_size,
            batch_size=self.batch_size,
            class_mode='categorical',
            subset='validation',
            shuffle=False
        )
        
        return train_generator, validation_generator
    
    def build_model(self):
        """Build MobileNetV2-based transfer learning model"""
        # Load pre-trained MobileNetV2
        base_model = MobileNetV2(
            weights='imagenet',
            include_top=False,
            input_shape=(self.img_size[0], self.img_size[1], 3)
        )
        
        # Freeze base model layers
        base_model.trainable = False
        
        # Add custom layers
        inputs = keras.Input(shape=(self.img_size[0], self.img_size[1], 3))
        x = base_model(inputs, training=False)
        x = layers.GlobalAveragePooling2D()(x)
        x = layers.Dropout(0.2)(x)
        x = layers.Dense(128, activation='relu')(x)
        x = layers.Dropout(0.5)(x)
        outputs = layers.Dense(self.num_classes, activation='softmax')(x)
        
        model = keras.Model(inputs, outputs)
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
        )
        
        self.model = model
        return model
    
    def train(self, train_generator, validation_generator, epochs=10):
        """Train the model"""
        if self.model is None:
            self.build_model()
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=3,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.2,
                patience=2,
                min_lr=0.00001
            ),
            keras.callbacks.ModelCheckpoint(
                'models/best_model.h5',
                monitor='val_accuracy',
                save_best_only=True
            )
        ]
        
        # Train the model
        history = self.model.fit(
            train_generator,
            validation_data=validation_generator,
            epochs=epochs,
            callbacks=callbacks,
            verbose=1
        )
        
        return history
    
    def fine_tune(self, train_generator, validation_generator, epochs=5):
        """Fine-tune the model by unfreezing some layers"""
        # Unfreeze the base model
        self.model.trainable = True
        
        # Freeze early layers, fine-tune later layers
        for layer in self.model.layers[:100]:
            layer.trainable = False
            
        # Recompile with lower learning rate
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.00001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        # Continue training
        history = self.model.fit(
            train_generator,
            validation_data=validation_generator,
            epochs=epochs,
            verbose=1
        )
        
        return history
    
    def save_model(self, path='models/mobilenet_model.h5'):
        """Save the trained model"""
        if self.model:
            self.model.save(path)
            print(f"Model saved to {path}")
            
            # Save class indices
            import json
            class_indices = {
                'biodegradable': 0,
                'recyclable': 1,
                'hazardous': 2
            }
            with open('models/class_indices.json', 'w') as f:
                json.dump(class_indices, f)

if __name__ == "__main__":
    # Create data directory structure if it doesn't exist
    # Expected structure:
    # data/
    #   biodegradable/
    #   recyclable/
    #   hazardous/
    
    trainer = WasteClassifierTrainer()
    
    # Prepare data
    train_gen, val_gen = trainer.prepare_data('data')
    
    # Build and train model
    trainer.build_model()
    history = trainer.train(train_gen, val_gen, epochs=10)
    
    # Fine-tune
    trainer.fine_tune(train_gen, val_gen, epochs=5)
    
    # Save final model
    trainer.save_model('models/mobilenet_model.h5')
    
    # Plot training history
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(history.history['accuracy'], label='Training Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.title('Model Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('Model Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('models/training_history.png')
    plt.show()