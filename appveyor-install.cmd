"%sdkverpath%" -q -version:"%sdkver%"
call setenv /x64

rem install python packages
pip install --cache-dir c:/egg_cache nose
pip install --cache-dir c:/egg_cache coverage
pip install --cache-dir c:/egg_cache numpy
pip install --cache-dir c:/egg_cache cython
pip install --cache-dir C:/egg_cache Sphinx

rem install traits
python setup.py develop