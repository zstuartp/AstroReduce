#!/bin/bash

REDUCE_VENV=reduce-venv # .gitignore is set to ignore "reduce-venv
VENV_RET=0
DEPI_RET=0

create_venv () { # Create the virtual environment
	virtualenv --no-site-packages --distribute $REDUCE_VENV
	VENV_RET=$?
	return $VENV_RET
}

install_deps () { # Install the pip dependencies
	echo "Installing virtual environment dependencies..."
	source $REDUCE_VENV/bin/activate &&\
	pip3 install -r ./requirements.txt
	DEPI_RET=$?
	return $DEPI_RET
}

# Check if we need to create the virtual environment
if [ ! -d "$REDUCE_VENV" ]; then
	echo "Creating the virtual environment in \"$REDUCE_VENV\"..."
	create_venv && install_deps
else
	echo "Virtual env already setup in \"$REDUCE_VENV\", updating..."
	install_deps
fi

# Pip failed to install the dependencies
if [ $DEPI_RET -ne 0 ]; then
	echo "Failed to install dependencies. Do you have \"pip3\" installed?"
fi


if [ $VENV_RET -ne 0 ]; then # No virtual env was created
	echo "No virtual envornment was created. Do you have the \"virtualenv\" python module installed?"
else 
	echo "Run \"source $REDUCE_VENV/bin/activate\" to activate the virtual env."
fi

exit $(($VENV_RET+$DEPI_RET))