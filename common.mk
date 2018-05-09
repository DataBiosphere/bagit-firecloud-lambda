SHELL=/bin/bash

ifeq ($(findstring python3.6, $(shell ls -ls /usr/bin/python* | grep python3.6 2>&1)),)
$(error Please install Python 3.6 on the system)
endif
