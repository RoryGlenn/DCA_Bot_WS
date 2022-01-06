# define Python user-defined exceptions
class Error(Exception):
    """Base class for other exceptions"""
    pass


class BaseOrderPrice(Error):
    """Raised when the base order price cannot be found"""
    pass

