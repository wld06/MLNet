import uuid
from collections.abc import Callable
from io import BytesIO

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import DatasetNotFoundError, InvalidOperationError
from app.core.storage import download_file, upload_file
from app.db.models import DatasetVersion
from app.services.dataset_service import get_dataset_or_404, get_version_or_404

# Datasets above this row count run the pipeline in Celery + stream WS progress.
LARGE_DATASET_ROWS = 100_000


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_latest_version(db: Session, dataset_id: int) -> DatasetVersion:
    version = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version_number.desc())
        .first()
    )
    if not version:
        raise DatasetNotFoundError(f"No versions found for dataset {dataset_id}")
    return version


def _load_df(storage_path: str, nrows: int | None = None) -> pd.DataFrame:
    buf = download_file(storage_path)
    return pd.read_csv(buf, nrows=nrows)


def _save_new_version(
    db: Session,
    dataset_id: int,
    df: pd.DataFrame,
    operation_type: str,
    parameters: dict,
    prev_version: DatasetVersion,
    label: str | None = None,
) -> DatasetVersion:
    buf = BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    key = f"datasets/{dataset_id}/versions/{uuid.uuid4()}.csv"
    upload_file(buf, key)

    new_ops_log = list(prev_version.operations_log or [])
    new_ops_log.append({"operation": operation_type, "parameters": parameters})

    version = DatasetVersion(
        dataset_id=dataset_id,
        version_number=prev_version.version_number + 1,
        storage_path=key,
        row_count=len(df),
        col_count=len(df.columns),
        operations_log=new_ops_log,
        label=label,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def _apply_single_op(df: pd.DataFrame, op_type: str, params: dict) -> pd.DataFrame:
    match op_type:
        case "drop_nulls":
            cols = params.get("columns")
            how = params.get("how", "any")
            return df.dropna(subset=cols if cols else None, how=how)

        case "fill_nulls":
            col = params["column"]
            strategy = params["strategy"]
            value = params.get("value")
            if strategy == "mean":
                df[col] = df[col].fillna(df[col].mean())
            elif strategy == "median":
                df[col] = df[col].fillna(df[col].median())
            elif strategy == "mode":
                mode = df[col].mode()
                df[col] = df[col].fillna(mode.iloc[0] if not mode.empty else np.nan)
            elif strategy == "constant":
                df[col] = df[col].fillna(value)
            else:
                raise InvalidOperationError(f"Unknown fill strategy: {strategy}")
            return df

        case "drop_duplicates":
            return df.drop_duplicates()

        case "cast_column":
            col = params["column"]
            dtype = params["dtype"]
            dtype_map = {"int": "Int64", "float": "float64", "str": "str", "bool": "bool"}
            df[col] = df[col].astype(dtype_map.get(dtype, dtype))
            return df

        case "rename_column":
            return df.rename(columns={params["old_name"]: params["new_name"]})

        case "drop_columns":
            return df.drop(columns=params["columns"], errors="ignore")

        case "normalize":
            cols = params["columns"]
            method = params["method"]
            for col in cols:
                if method == "minmax":
                    mn, mx = df[col].min(), df[col].max()
                    df[col] = (df[col] - mn) / (mx - mn) if mx != mn else 0.0
                elif method == "standard":
                    mean, std = df[col].mean(), df[col].std()
                    df[col] = (df[col] - mean) / std if std != 0 else 0.0
                elif method == "robust":
                    med = df[col].median()
                    iqr = df[col].quantile(0.75) - df[col].quantile(0.25)
                    df[col] = (df[col] - med) / iqr if iqr != 0 else 0.0
                else:
                    raise InvalidOperationError(f"Unknown normalize method: {method}")
            return df

        case "encode":
            col = params["column"]
            method = params["method"]
            if method == "label":
                df[col] = df[col].astype("category").cat.codes
            elif method == "onehot":
                dummies = pd.get_dummies(df[col], prefix=col)
                df = pd.concat([df.drop(columns=[col]), dummies], axis=1)
            elif method == "ordinal":
                cats = params.get("categories") or df[col].dropna().unique().tolist()
                df[col] = df[col].map({c: i for i, c in enumerate(cats)})
            else:
                raise InvalidOperationError(f"Unknown encode method: {method}")
            return df

        case "filter_rows":
            col = params["column"]
            op = params["operator"]
            val = params["value"]
            ops_map = {
                "eq": lambda: df[col] == val,
                "ne": lambda: df[col] != val,
                "gt": lambda: df[col] > val,
                "lt": lambda: df[col] < val,
                "gte": lambda: df[col] >= val,
                "lte": lambda: df[col] <= val,
                "isin": lambda: df[col].isin(val if isinstance(val, list) else [val]),
                "notin": lambda: ~df[col].isin(val if isinstance(val, list) else [val]),
                "contains": lambda: df[col].astype(str).str.contains(str(val), na=False),
            }
            builder = ops_map.get(op)
            if builder is None:
                raise InvalidOperationError(f"Unknown filter operator: {op}")
            return df[builder()]

        case "string_ops":
            col = params["column"]
            op = params["operation"]
            target = params.get("new_column") or col
            str_map = {
                "lower": lambda: df[col].str.lower(),
                "upper": lambda: df[col].str.upper(),
                "strip": lambda: df[col].str.strip(),
                "title": lambda: df[col].str.title(),
            }
            builder = str_map.get(op)
            if builder is None:
                raise InvalidOperationError(f"Unknown string operation: {op}")
            df[target] = builder()
            return df

        case "replace_values":
            col = params["column"]
            df[col] = df[col].replace(params["mapping"])
            return df

        case _:
            raise InvalidOperationError(f"Unknown operation: {op_type}")


# ─── Inspection ───────────────────────────────────────────────────────────────

def get_quality(db: Session, dataset_id: int) -> dict:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)

    issues: list[dict] = []
    null_cols: dict[str, int] = {}

    for col in df.columns:
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            null_cols[col] = null_count
            issues.append({
                "type": "null_values",
                "column": col,
                "count": null_count,
                "pct": round(null_count / len(df) * 100, 2),
            })

    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        issues.append({"type": "duplicates", "count": dup_count})

    for col in df.columns:
        if df[col].dtype == object:
            try:
                pd.to_numeric(df[col].dropna())
                issues.append({"type": "type_mismatch", "column": col, "suggestion": "cast to numeric"})
            except (ValueError, TypeError):
                pass

    return {
        "version": version.version_number,
        "row_count": len(df),
        "col_count": len(df.columns),
        "duplicate_count": dup_count,
        "null_columns": null_cols,
        "issues": issues,
        "issue_count": len(issues),
    }


def get_distribution(db: Session, dataset_id: int, col: str) -> dict:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)

    if col not in df.columns:
        raise InvalidOperationError(f"Column '{col}' not found")

    series = df[col]
    null_count = int(series.isna().sum())

    if pd.api.types.is_numeric_dtype(series):
        counts, edges = np.histogram(series.dropna(), bins=20)
        return {
            "type": "numeric",
            "column": col,
            "null_count": null_count,
            "min": float(series.min()),
            "max": float(series.max()),
            "mean": float(series.mean()),
            "std": float(series.std()),
            "histogram": {
                "counts": counts.tolist(),
                "edges": [round(e, 6) for e in edges.tolist()],
            },
        }

    value_counts = series.dropna().value_counts().head(20)
    return {
        "type": "categorical",
        "column": col,
        "null_count": null_count,
        "unique_count": int(series.nunique()),
        "value_counts": {str(k): int(v) for k, v in value_counts.items()},
    }


def get_outliers(db: Session, dataset_id: int, col: str) -> dict:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)

    if col not in df.columns:
        raise InvalidOperationError(f"Column '{col}' not found")

    series = df[col].dropna()
    if not pd.api.types.is_numeric_dtype(series):
        raise InvalidOperationError(f"Column '{col}' is not numeric")

    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    outlier_mask = (df[col] < lower) | (df[col] > upper)
    outlier_count = int(outlier_mask.sum())

    return {
        "column": col,
        "method": "IQR",
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower_bound": lower,
        "upper_bound": upper,
        "outlier_count": outlier_count,
        "outlier_pct": round(outlier_count / len(df) * 100, 2),
        "sample_outliers": df.loc[outlier_mask, col].head(10).tolist(),
    }


def get_correlations(db: Session, dataset_id: int) -> dict:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)

    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        return {"columns": [], "matrix": []}

    corr = numeric_df.corr()
    return {
        "columns": corr.columns.tolist(),
        "matrix": [
            [round(v, 4) if not np.isnan(v) else None for v in row]
            for row in corr.values.tolist()
        ],
    }


def get_duplicates(db: Session, dataset_id: int) -> dict:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)

    dup_mask = df.duplicated(keep=False)
    dup_count = int(df.duplicated().sum())

    return {
        "duplicate_count": dup_count,
        "total_rows": len(df),
        "duplicate_pct": round(dup_count / len(df) * 100, 2) if len(df) else 0,
        "sample": df[dup_mask].head(10).to_dict(orient="records"),
    }


# ─── Mutations ────────────────────────────────────────────────────────────────

def drop_nulls(db: Session, dataset_id: int, columns: list[str] | None, how: str) -> DatasetVersion:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)
    df = df.dropna(subset=columns if columns else None, how=how)
    return _save_new_version(db, dataset_id, df, "drop_nulls", {"columns": columns, "how": how}, version)


def fill_nulls(db: Session, dataset_id: int, column: str, strategy: str, value) -> DatasetVersion:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)
    params = {"column": column, "strategy": strategy, "value": value}
    df = _apply_single_op(df.copy(), "fill_nulls", params)
    return _save_new_version(db, dataset_id, df, "fill_nulls", params, version)


def fill_nulls_bulk(db: Session, dataset_id: int, operations: list[dict]) -> DatasetVersion:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)
    for op in operations:
        df = _apply_single_op(df.copy(), "fill_nulls", op)
    return _save_new_version(db, dataset_id, df, "fill_nulls_bulk", {"operations": operations}, version)


def drop_duplicates(db: Session, dataset_id: int) -> DatasetVersion:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)
    df = df.drop_duplicates()
    return _save_new_version(db, dataset_id, df, "drop_duplicates", {}, version)


def cast_column(db: Session, dataset_id: int, column: str, dtype: str) -> DatasetVersion:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)
    params = {"column": column, "dtype": dtype}
    df = _apply_single_op(df.copy(), "cast_column", params)
    return _save_new_version(db, dataset_id, df, "cast_column", params, version)


def rename_column(db: Session, dataset_id: int, old_name: str, new_name: str) -> DatasetVersion:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)
    if old_name not in df.columns:
        raise InvalidOperationError(f"Column '{old_name}' not found")
    df = df.rename(columns={old_name: new_name})
    return _save_new_version(db, dataset_id, df, "rename_column", {"old_name": old_name, "new_name": new_name}, version)


def drop_columns(db: Session, dataset_id: int, columns: list[str]) -> DatasetVersion:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)
    df = df.drop(columns=columns, errors="ignore")
    return _save_new_version(db, dataset_id, df, "drop_columns", {"columns": columns}, version)


def normalize(db: Session, dataset_id: int, columns: list[str], method: str) -> DatasetVersion:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)
    params = {"columns": columns, "method": method}
    df = _apply_single_op(df.copy(), "normalize", params)
    return _save_new_version(db, dataset_id, df, "normalize", params, version)


def encode(
    db: Session, dataset_id: int, column: str, method: str, categories: list | None = None
) -> DatasetVersion:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)
    params = {"column": column, "method": method, "categories": categories}
    df = _apply_single_op(df.copy(), "encode", params)
    return _save_new_version(db, dataset_id, df, "encode", params, version)


def filter_rows(db: Session, dataset_id: int, column: str, operator: str, value) -> DatasetVersion:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)
    params = {"column": column, "operator": operator, "value": value}
    df = _apply_single_op(df.copy(), "filter_rows", params)
    return _save_new_version(db, dataset_id, df, "filter_rows", params, version)


def string_ops(
    db: Session, dataset_id: int, column: str, operation: str, new_column: str | None
) -> DatasetVersion:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)
    params = {"column": column, "operation": operation, "new_column": new_column}
    df = _apply_single_op(df.copy(), "string_ops", params)
    return _save_new_version(db, dataset_id, df, "string_ops", params, version)


def replace_values(db: Session, dataset_id: int, column: str, mapping: dict) -> DatasetVersion:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)
    params = {"column": column, "mapping": mapping}
    df = _apply_single_op(df.copy(), "replace_values", params)
    return _save_new_version(db, dataset_id, df, "replace_values", params, version)


# ─── Pipeline ─────────────────────────────────────────────────────────────────

def preview_operations(db: Session, dataset_id: int, operations: list[dict]) -> dict:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path, nrows=settings.CLEANING_PREVIEW_ROWS)

    for op in operations:
        df = _apply_single_op(df.copy(), op["operation"], op.get("parameters", {}))

    return {
        "columns": df.columns.tolist(),
        "rows": df.values.tolist(),
        "row_count": len(df),
        "col_count": len(df.columns),
    }


def apply_pipeline(
    db: Session,
    dataset_id: int,
    operations: list[dict],
    label: str | None,
    on_progress: "Callable[[int, int, str], None] | None" = None,
) -> DatasetVersion:
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    df = _load_df(version.storage_path)

    total = len(operations)
    for idx, op in enumerate(operations, start=1):
        df = _apply_single_op(df.copy(), op["operation"], op.get("parameters", {}))
        if on_progress is not None:
            on_progress(idx, total, op["operation"])

    buf = BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    key = f"datasets/{dataset_id}/versions/{uuid.uuid4()}.csv"
    upload_file(buf, key)

    new_ops_log = list(version.operations_log or [])
    for op in operations:
        new_ops_log.append({"operation": op["operation"], "parameters": op.get("parameters", {})})

    new_version = DatasetVersion(
        dataset_id=dataset_id,
        version_number=version.version_number + 1,
        storage_path=key,
        row_count=len(df),
        col_count=len(df.columns),
        operations_log=new_ops_log,
        label=label,
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    return new_version


def is_large_dataset(db: Session, dataset_id: int) -> bool:
    """True when the latest version exceeds the async pipeline threshold."""
    get_dataset_or_404(db, dataset_id)
    version = _get_latest_version(db, dataset_id)
    return (version.row_count or 0) > LARGE_DATASET_ROWS


def get_history(db: Session, dataset_id: int) -> list[dict]:
    get_dataset_or_404(db, dataset_id)
    versions = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version_number)
        .all()
    )
    return [
        {
            "version": v.version_number,
            "label": v.label,
            "row_count": v.row_count,
            "col_count": v.col_count,
            "created_at": v.created_at.isoformat(),
            "operations_log": v.operations_log or [],
        }
        for v in versions
    ]


def rollback(db: Session, dataset_id: int, version_number: int) -> DatasetVersion:
    get_dataset_or_404(db, dataset_id)
    target = get_version_or_404(db, dataset_id, version_number)
    latest = _get_latest_version(db, dataset_id)

    df = _load_df(target.storage_path)
    buf = BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    key = f"datasets/{dataset_id}/versions/{uuid.uuid4()}.csv"
    upload_file(buf, key)

    new_version = DatasetVersion(
        dataset_id=dataset_id,
        version_number=latest.version_number + 1,
        storage_path=key,
        row_count=target.row_count,
        col_count=target.col_count,
        operations_log=list(target.operations_log or []),
        label=f"rollback_to_v{version_number}",
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    return new_version
