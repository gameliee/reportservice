import pytest
from pydantic import ValidationError
from ..models import ContentModelUpdate


def test_contentmodelupdate():
    # this model should be valid
    ContentModelUpdate(cc=["abc@123.org"])
    ContentModelUpdate(to=["abc@123.org"])
    ContentModelUpdate(to=None)

    # this model should be invalid
    with pytest.raises(ValidationError):
        ContentModelUpdate(to=[])
