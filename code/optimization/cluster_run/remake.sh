#!/bin/bash

module unload gnu8
module load intel/19.0.2.187
module load boost/1.70.0

dos2unix main.cpp
sed -i 's/define BORG_RUN_TYPE 0/define BORG_RUN_TYPE 2/' main.cpp
sed -i 's/define BORG_RUN_TYPE 1/define BORG_RUN_TYPE 2/' main.cpp
sed -i 's+#include "./../../misc/borg/borg.h"+//#include "./../../misc/borg/borg.h"+' main.cpp
sed -i 's+//#include "./../../misc/borg/borgms.h"+#include "./../../misc/borg/borgms.h"+' main.cpp
sed -i 's+// #include "./../../misc/borg/borgms.h"+#include "./../../misc/borg/borgms.h"+' main.cpp
make problem_borgms

cp main.cpp main_sensitivity.cpp
sed -i 's/define SENSITIVITY_ANALYSIS 0/define SENSITIVITY_ANALYSIS 1/' main_sensitivity.cpp
make problem_sensitivity_borgms

cp main.cpp main_retest.cpp
sed -i 's/define BORG_RUN_TYPE 2/define BORG_RUN_TYPE 0/' main_retest.cpp
make problem_retest

