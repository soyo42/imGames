#!/bin/bash

outFile='out'

python2.7 ./loveLetter.py -a init -v -l .llStore1 \
    && python2.7 ./loveLetter.py -a init -v -m ${outFile} -l .llStore2 \
    && python2.7 ./loveLetter.py -a init -v -m ${outFile} -l .llStore3 \
    && python2.7 ./loveLetter.py -a init -v -m ${outFile} -l .llStore1 \
    && python2.7 ./loveLetter.py -a turn -v -m ${outFile} -l .llStore2 \
    && python2.7 ./loveLetter.py -a turn -v -m ${outFile} -l .llStore1 
