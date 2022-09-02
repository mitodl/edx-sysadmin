#!/bin/bash
set -e

source /edx/app/edxapp/venvs/edxapp/bin/activate

cd /edx/app/edxapp/edx-platform
mkdir -p reports

pip install -r ./requirements/edx/testing.txt
pip install -r ./requirements/edx/paver.txt
sudo npm install -g rtlcss

mkdir -p test_root  # for edx

paver update_assets lms --settings=test_static_optimized

cp test_root/staticfiles/lms/webpack-stats.json test_root/staticfiles/webpack-stats.json
cp -r test_root/ /edx-sysadmin/test_root

cd /edx-sysadmin
pip install -e .

# output the packages which are installed for logging
pip freeze

set +e

# We're running pycodestyle directly here since pytest-pep8 hasn't been updated in a while and has a bug
# linting this project's code. pylint is also run directly since it seems cleaner to run them both
# separately than to run one as a plugin and one by itself.
echo "Running pycodestyle"
pycodestyle edx_sysadmin tests
PYCODESTYLE_SUCCESS=$?

echo "Running pylint"
(cd /edx/app/edxapp/edx-platform; pylint /edx-sysadmin/edx_sysadmin)
PYLINT_SUCCESS=$?

if [[ $PYCODESTYLE_SUCCESS -ne 0 ]]
then
    echo "pycodestyle exited with a non-zero status"
    exit $PYCODESTYLE_SUCCESS
fi
if [[ $PYLINT_SUCCESS -ne 0 ]]
then
    echo "pylint exited with a non-zero status"
    exit $PYLINT_SUCCESS
fi

echo "Running tests"
pytest
PYTEST_SUCCESS=$?

if [[ $PYTEST_SUCCESS -ne 0 ]]
then
    echo "pytest exited with a non-zero status"
    exit $PYTEST_SUCCESS
fi

set -e
coverage xml

