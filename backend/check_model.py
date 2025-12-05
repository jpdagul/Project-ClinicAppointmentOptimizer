"""
Quick script to check if the model can be loaded and provide helpful error messages.
Run this to diagnose model compatibility issues.
"""
import sys
from pathlib import Path

# Add model directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / 'model'
sys.path.insert(0, str(MODEL_DIR))

def check_model():
    """Check if the model can be loaded."""
    import joblib
    import sklearn
    
    print(f"scikit-learn version: {sklearn.__version__}")
    print(f"Model directory: {MODEL_DIR / 'models'}")
    
    model_path = MODEL_DIR / 'models' / 'gradient_boosting_model.pkl'
    alt_path = MODEL_DIR / 'models' / 'gradient_boosting.pkl'
    
    # Check which model file exists
    if model_path.exists():
        print(f"Found model: {model_path}")
        test_path = model_path
    elif alt_path.exists():
        print(f"Found model: {alt_path}")
        test_path = alt_path
    else:
        print("❌ ERROR: No model file found!")
        print(f"   Expected: {model_path}")
        print(f"   Or: {alt_path}")
        print("\n   Solution: Train the model first:")
        print("   cd model && python main.py")
        return False
    
    # Try to load the model
    try:
        print("\nAttempting to load model...")
        model = joblib.load(test_path)
        print("✅ SUCCESS: Model loaded successfully!")
        print(f"   Model type: {type(model)}")
        return True
    except AttributeError as e:
        if 'CyHalfBinomialLoss' in str(e) or '__pyx_unpickle' in str(e):
            print("❌ ERROR: Model version mismatch!")
            print(f"   Error: {e}")
            print("\n   Solution: Retrain the model with current scikit-learn version:")
            print("   cd model && python main.py")
            return False
        else:
            print(f"❌ ERROR: {e}")
            return False
    except Exception as e:
        print(f"❌ ERROR: Failed to load model: {e}")
        print("\n   Solution: Retrain the model:")
        print("   cd model && python main.py")
        return False

if __name__ == "__main__":
    success = check_model()
    sys.exit(0 if success else 1)

