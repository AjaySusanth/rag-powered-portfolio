import pytest

@pytest.fixture
def anyio_backend() -> str:
    """
    Specifies the backend for AnyIO tests.
    We restrict it to 'asyncio' because we do not use 'trio' in our stack.
    """
    return "asyncio"
