from src.train_model import train_and_select_model
from src.evaluate_model import evaluate_saved_model

if __name__ == "__main__":
    print("Training and Evaluating Baseline No-Show Model...")
    model_path = train_and_select_model()  # <- returns the saved model’s path
    evaluate_saved_model(model_path)       # <– evaluates the same one
