Internal notes on how to do a release
=====================================

$ git checkout -b release/0.1.0
# update version info in layeredconfig/__init__.py
$ git commit -am "Final release prep"
# push changes so that travis-ci/appveyor can test the bits to be released
$ git push --set-upstream origin release/0.1.0
# tag release and push to github, to make this tree be a "release"
$ git tag -a "v0.1.0" -m "Initial release"
$ git push --tags # makes the release show up in Github
# register a new version on pypi and upload it
$ python setup.py register
$ python setup.py sdist
$ python setup.py bdist_wheel --universal
$ twine upload dist/layeredconfig-0.1.0.tar.gz dist/layeredconfig-0.1.0-py2.py3-none-any.whl
# start the next cycle
$ git checkout master
$ git merge release/0.1.0
# update layeredconfig/__init__.py to eg version=0.1.1.dev1 and ideally also appveyor.yml
$ git commit -m "start of next iteration" layeredconfig/__init__.py
$ git push
