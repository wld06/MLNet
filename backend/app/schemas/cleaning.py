from pydantic import BaseModel


class FillNullsRequest(BaseModel):
    column: str
    strategy: str  # mean, median, mode, constant
    value: str | float | int | None = None


class DropNullsRequest(BaseModel):
    columns: list[str] | None = None
    how: str = "any"  # any, all


class CastColumnRequest(BaseModel):
    column: str
    dtype: str  # int, float, str, bool


class RenameColumnRequest(BaseModel):
    old_name: str
    new_name: str


class DropColumnsRequest(BaseModel):
    columns: list[str]


class NormalizeRequest(BaseModel):
    columns: list[str]
    method: str  # minmax, standard, robust


class EncodeRequest(BaseModel):
    column: str
    method: str  # onehot, label, ordinal


class FilterRowsRequest(BaseModel):
    column: str
    operator: str  # eq, ne, gt, lt, gte, lte, isin, notin, contains
    value: str | float | int | list


class StringOpsRequest(BaseModel):
    column: str
    operation: str  # lower, upper, strip, title
    new_column: str | None = None


class ReplaceValuesRequest(BaseModel):
    column: str
    mapping: dict


class PreviewRequest(BaseModel):
    operations: list[dict]


class ApplyPipelineRequest(BaseModel):
    operations: list[dict]
    label: str | None = None


class CleaningOperationRead(BaseModel):
    id: int
    operation_type: str
    parameters: dict | None
    status: str
    rows_affected: int | None
