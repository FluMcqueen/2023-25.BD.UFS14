import pytest
from jsonschema import validate

schema = {
    "type" : "object",
    "properties" : {
        "price" : {"type" : "number"},
        "name" : {"type" : "string"},
    },
}

def val_wrapper(instance, schema):
    try:
        validate(instance, schema)
        return True
    except:
        return False

def func(x):
    return x + 1

def test_answer():
    assert func(4) == 5

def test_succo():
    assert val_wrapper(instance={"name" : "Eggs", "price" : 34.99}, schema=schema)

def test_errato():
    assert val_wrapper(instance={"name" : "Eggs", "price" : "Invalid"}, schema=schema,) == False

def test_funcoutputsnapshot(snapshot):
    snapshot.snapshot_dir = "snapshot"
    pierino = func(5)
    snapshot.assert_match(str(pierino), "foo_output.txt")
