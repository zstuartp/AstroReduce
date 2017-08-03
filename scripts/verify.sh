#!/bin/bash

_TEST_DATA_DIR="test-data"
_TEST_LOG_DIR="$_TEST_DATA_DIR/log"

echo "Setting up environment..."
mkdir -p $_TEST_DATA_DIR \
		$_TEST_LOG_DIR \
		$_TEST_DATA_DIR/flats \
		$_TEST_DATA_DIR/darks \
		$_TEST_DATA_DIR/lights \
		$_TEST_DATA_DIR/mdarks \
		$_TEST_DATA_DIR/mflats \
		$_TEST_DATA_DIR/output

rm -f $_TEST_DATA_DIR/output/*.fts

python3 -c "
import reduce
test_data_dir=\"$_TEST_DATA_DIR/\"
`cat reduce-test.py`"

TEST_STATUS=$?

mv *.log $_TEST_LOG_DIR

exit $TEST_STATUS
