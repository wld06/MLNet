from sklearn.pipeline import Pipeline


def build_pipeline(estimator, preprocessor=None) -> Pipeline:
    steps = []
    if preprocessor:
        steps.append(("preprocessor", preprocessor))
    steps.append(("estimator", estimator))
    return Pipeline(steps)
