#! /usr/bin/env bash

echo '> Producing mapping with capped at 4 elinks'
 ./produce_mapping.py --cfg config/220719_max_4elinks.yml
echo '> Producing mapping with capped at 5 elinks'
 ./produce_mapping.py --cfg config/220719_max_5elinks.yml
echo '> Producing mapping without capping'
 ./produce_mapping.py --cfg config/220719_no_max.yml
