import pytest
from jsonschema import validate

schema = {
    "type" : "object",
    "properties" : {
        "price" : {"type" : "number"},
        "name" : {"type" : "string"},
    },
}

def func(x):
    return x + 1

def test_answer():
    assert func(4) == 5

def test_succo():
    validate(instance={"name" : "Eggs", "price" : 34.99}, schema=schema)
