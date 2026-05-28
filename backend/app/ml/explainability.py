import shap


def compute_shap_values(model, X_sample) -> dict:
    try:
        explainer = shap.TreeExplainer(model)
    except Exception:
        explainer = shap.KernelExplainer(model.predict, X_sample[:50])

    shap_values = explainer.shap_values(X_sample)
    if isinstance(shap_values, list):
        # multiclass: use class 1
        shap_values = shap_values[1]

    mean_abs = abs(shap_values).mean(axis=0)
    return {
        "feature_importance": dict(zip(X_sample.columns.tolist(), mean_abs.tolist())),
        "shap_values": shap_values.tolist(),
    }
