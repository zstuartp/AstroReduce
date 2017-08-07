PROGRAM_NAME=AstroReduce
PROGRAM_SHORT_NAME=ar
VENV_DIR=reduce-venv
VERIFY_SCRIPT=scripts/verify.sh
AR_PEX_NAME=$(PROGRAM_SHORT_NAME).pex
BUILD_DIR=build
REQ_PYTHON_VER=python3
SOURCES=\
	astroreduce/*.py \
	setup.py

default:
	@echo "Run \"make venv\" first, then activate the virtualenv with \"source $(VENV_DIR)/bin/activate\""
	@echo "Once you have the virtual environment activated, run \"make build\""

verify:
	@bash $(VERIFY_SCRIPT)

# Virtual environment setup/update
venv: $(VENV_DIR)/bin/activate

$(VENV_DIR)/bin/activate: requirements-build.txt
	@echo "Setting up virtualenv in $(VENV_DIR)"
	@test -d venv || virtualenv $(VENV_DIR)
	@$(VENV_DIR)/bin/pip3 install -Ur requirements-build.txt
	@touch $(VENV_DIR)/bin/activate
	@echo "Done. Run \"source $(VENV_DIR)/bin/activate\" to activate the virtualenv"

# Build the portable python executable (.pex) package 
build: $(AR_PEX_NAME)

$(AR_PEX_NAME): $(SOURCES)
	@echo "Building the portable python executable as \"$(AR_PEX_NAME)\"..."
	@mkdir -p build
	@pex . --python=$(REQ_PYTHON_VER) -v -r requirements.txt -e astroreduce -o $(AR_PEX_NAME) --cache-dir=$(BUILD_DIR)/pex-cache
	@echo "Done."
	@echo "You can run $(PROGRAM_NAME) simply as \"./$(AR_PEX_NAME)\""

clean-build:
	@rm -rf $(BUILD_DIR)
	@rm -f $(AR_PEX_NAME)

clean-venv:
	@rm -rf $(VENV_DIR)

clean: clean-build

dist-clean: clean clean-venv
