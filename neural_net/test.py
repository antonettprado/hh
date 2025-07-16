# test_model_save.py
import tensorflow as tf
from pathlib import Path

# 1) Simple toy model
inputs = tf.keras.Input(shape=(4,))
x = tf.keras.layers.Dense(8, activation='relu')(inputs)
outputs = tf.keras.layers.Dense(1, activation='sigmoid')(x)
model = tf.keras.Model(inputs, outputs)

model.compile(optimizer='adam', loss='binary_crossentropy')

# Dummy data to fit quickly
import numpy as np
X = np.random.rand(100, 4)
y = np.random.randint(0, 2, size=(100, 1))

model.fit(X, y, epochs=2, verbose=2)

# ============
# 1) Save full model: SavedModel format
# ============
saved_model_dir = Path("test_saved_model")
model.save(saved_model_dir)
print(f"✅ Saved full model to {saved_model_dir.resolve()}")

# Reload it
reloaded1 = tf.keras.models.load_model(saved_model_dir)
print(f"✅ Reloaded full model — summary:")
reloaded1.summary()

# ============
# 2) Save full model: HDF5 format
# ============
h5_file = Path("test_model.h5")
model.save(h5_file)
print(f"✅ Saved full model to {h5_file.resolve()}")

# Reload it
reloaded2 = tf.keras.models.load_model(h5_file)
print(f"✅ Reloaded HDF5 model — summary:")
reloaded2.summary()

# ============
# 3) Save weights only
# ============
weights_file = Path("test_weights.h5")
model.save_weights(weights_file)
print(f"✅ Saved weights to {weights_file.resolve()}")

# Rebuild same model structure
inputs = tf.keras.Input(shape=(4,))
x = tf.keras.layers.Dense(8, activation='relu')(inputs)
outputs = tf.keras.layers.Dense(1, activation='sigmoid')(x)
model2 = tf.keras.Model(inputs, outputs)
model2.compile(optimizer='adam', loss='binary_crossentropy')

model2.load_weights(weights_file)
print(f"✅ Loaded weights into new model — summary:")
model2.summary()