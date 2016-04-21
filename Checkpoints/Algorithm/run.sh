#!/bin/bash
cat sqlite_load.sql | sqlite3 lunchapp.db
./algorithm.py