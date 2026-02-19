import numpy as np

def evaluate_thresholds(y_proba, simulator):
    thresholds = np.linspace(0.1, 0.9, 50)
    results = []

    for t in thresholds:
        y_pred = (y_proba > t).astype(int)

        metrics = simulator.run(y_pred)
        results.append({
            "threshold": t,
            "avg_wait": metrics["avg_wait"],
            "overflow": metrics["overflow"]
        })

    return results