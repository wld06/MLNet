class MLNestException(Exception):
    pass


class DatasetNotFoundError(MLNestException):
    pass


class DatasetVersionNotFoundError(MLNestException):
    pass


class ExperimentNotFoundError(MLNestException):
    pass


class RunNotFoundError(MLNestException):
    pass


class DeploymentNotFoundError(MLNestException):
    pass


class DatasetTooLargeError(MLNestException):
    pass


class InvalidOperationError(MLNestException):
    pass


class StorageError(MLNestException):
    pass
