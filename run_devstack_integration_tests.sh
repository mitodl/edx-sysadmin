#!/bin/bash
set -e

source /edx/app/edxapp/venvs/edxapp/bin/activate

cd /edx/app/edxapp/edx-platform
mkdir -p reports

pip install -r ./requirements/edx/testing.txt
pip install -r ./requirements/edx/paver.txt
sudo npm install -g rtlcss
paver update_assets lms --settings=test_static_optimized
paver update_assets cms --settings=test_static_optimized
echo '---------------------------pwd--------------------'
pwd
cp -r test_root/ /edx-sysadmin/test_root
ls test_root/
echo '-------------------------------------------------'
ls /edx-sysadmin/test_root
echo '-------------------------------------------------'
cp test_root/staticfiles/lms/webpack-stats.json test_root/staticfiles/webpack-stats.json
mkdir -p /edx-sysadmin/test_root/staticfiles
cp test_root/staticfiles/lms/webpack-stats.json /edx-sysadmin/test_root/staticfiles/webpack-stats.json
echo '---------------------------pwd--------------------'
ls /edx/app/edxapp/edx-platform/test_root/staticfiles/
echo '---------------------------pwd--------------------'
ls /edx-sysadmin/test_root/staticfiles/
echo '-------------------------------------------------'
ls /edx/app/edxapp/edx-platform/test_root/staticfiles/lms
echo '-------------------------------------------------'

cat test_root/staticfiles/lms/webpack-stats.json
echo '-------------------------------------------------'
cat test_root/staticfiles/webpack-stats.json
echo '-------------------------------------------------'

cd /edx-sysadmin
pip install -e .

# Install codecov so we can upload code coverage results
pip install codecov

# output the packages which are installed for logging
pip freeze

mkdir -p test_root  # for edx

set +e

# We're running pycodestyle directly here since pytest-pep8 hasn't been updated in a while and has a bug
# linting this project's code. pylint is also run directly since it seems cleaner to run them both
# separately than to run one as a plugin and one by itself.
echo "Running tests"
pytest
PYTEST_SUCCESS=$?
echo "Running pycodestyle"
pycodestyle edx_sysadmin tests
PYCODESTYLE_SUCCESS=$?
echo "Running pylint"

(cd /edx/app/edxapp/edx-platform; pylint /edx-sysadmin/edx_sysadmin)
PYLINT_SUCCESS=$?

if [[ $PYTEST_SUCCESS -ne 0 ]]
then
    echo "pytest exited with a non-zero status"
    exit $PYTEST_SUCCESS
fi
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
