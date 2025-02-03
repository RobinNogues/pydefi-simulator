from typing import Any, ClassVar


class SingletonMeta(type):
    """Metaclass for singletons."""

    _instances: ClassVar[dict[type, Any]] = {}

    def __call__(cls, *args, **kwargs):  # noqa: ANN204
        """Create a new instance or return an existing one."""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
