#!/bin/bash
python make_sqlite.py $1 && python dump_to_sqlite.py $1
