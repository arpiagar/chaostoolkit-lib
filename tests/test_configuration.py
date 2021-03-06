# -*- coding: utf-8 -*-
import os

import pytest

from chaoslib.configuration import load_configuration


def test_should_load_configuration():
    os.environ["KUBE_TOKEN"] = "value2"
    config = load_configuration({
        "token1": "value1",
        "token2": {
            "type": "env",
            "key": "KUBE_TOKEN"
        }
    })

    assert config["token1"] == "value1"
    assert config["token2"] == "value2"
