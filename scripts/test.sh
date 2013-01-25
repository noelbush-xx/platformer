#!/usr/bin/env bash

nosetests -sv --nologcapture --logging-level=DEBUG --logging-filter=platformer.tests
