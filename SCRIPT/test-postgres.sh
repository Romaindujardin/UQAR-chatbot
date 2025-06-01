#!/bin/bash
apptainer exec docker://postgres:15 /bin/bash -c "echo Testing PostgreSQL"
