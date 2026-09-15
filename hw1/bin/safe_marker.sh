#!/usr/bin/env bash

if [[ $# -ne 1 || "$1" != "course-marker" ]]; then
    echo "Invalid"
    exit 1
fi

touch ~/csce465-agentsec/hw1/markers/marker.txt
exit 0
