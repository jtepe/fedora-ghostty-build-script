# Ghostty Management Script

This project consists of a single Python script in install.py that is used to manage an installation
of the Ghostty terminal application on Fedora Linux.
It downloads, builds, and installs Ghostty on demand, providing a set of commandline parameters to
drive and customize the process.

## Project Guidelines

* All code is to go into install.py
* Use the most recent Python version 3.13. Assume Python is installed
* uv is used exclusively to manage dependencies, drive the build, and execute the script. Don't use pip
* No tests need to be written
* Colored logging must be used as feedback to the user
* Adding external dependencies is to be avoided unless necessary to implement a feature
* If a dependency `foo` is needed use `uv add --script install.py 'foo'` to add it to the script
* Use type hints throughout
