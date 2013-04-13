#!/usr/bin/env bash

#nosetests -sv --nologcapture --logging-level=DEBUG --logging-filter=platformer.tests
nosetests -s --nologcapture --logging-filter=platformer.tests
