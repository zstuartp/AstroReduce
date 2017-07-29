#!/bin/sh

REDUCE_VENV=reduce-venv # .gitignore is set to ignore "reduce-venv

install_deps () {
	echo "Installing virtual environment dependencies..."
	source $REDUCE_VENV/bin/activate &&\
	pip3 install -r ./requirements.txt
}

# Check if we need to create the virtual environment
if [ ! -d "$REDUCE_VENV" ]; then
	echo "Creating the virtual environment in \"$REDUCE_VENV\"..."
	virtualenv --no-site-packages --distribute $REDUCE_VENV &&\
	install_deps
	echo "Done."
else
	echo "Virtual env already setup in \"$REDUCE_VENV\", updating..."
	install_deps
	echo "Done."
fi

echo "Run \"source $REDUCE_VENV/bin/activate\" to activate the virtual env"
