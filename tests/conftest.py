import pytest
from app.command.info import ReplicationRole, init_info


@pytest.fixture(autouse=True)
def initialize_info():
    init_info(role=ReplicationRole.MASTER)
