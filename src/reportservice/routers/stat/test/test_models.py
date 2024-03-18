import pytest
import json
from pydantic import BaseModel, ValidationError
from bson import json_util
from ..models import validate_query, MongoQueryStr, QueryParamters


def test_validate_query():
    # Test the function with a valid query
    valid_query = '{"name": "John Doe"}'
    assert validate_query(valid_query) == json.loads(valid_query)

    valid_query = {"name": "John Doe"}
    assert validate_query(valid_query) == valid_query

    # Test the function with an invalid query
    invalid_query = '{"name": "John Doe",}'

    with pytest.raises(json.decoder.JSONDecodeError):
        validate_query(invalid_query)


class DemoModel(BaseModel):
    value: MongoQueryStr


def test_MongoQueryStr():
    # Test the MongoQueryStr type with a valid query
    valid_query = '{"name": "John Doe"}'
    a = DemoModel(value=valid_query)
    assert a.value == json.loads(valid_query)

    # Test the MongoQueryStr type with an invalid query
    invalid_query = '{"name": "John Doe",}'
    with pytest.raises(ValidationError):
        DemoModel(value=invalid_query)


def test_QueryParamters():
    # Test the QueryParamters type with a valid query
    valid_query = '{"name": "John Doe"}'
    a = QueryParamters(staffcodes=["123456"], custom_query=valid_query)
    bson_encoded = json_util.dumps(a.model_dump())
    assert bson_encoded is not None
