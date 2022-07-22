# Contributing to the project

Our project's main branch is protected, meaning you cannot directly push code to it. Instead, you must add code to it VIA a pull request.

## Steps to Contributing

### Installing the Project with Poetry

Before you are able to contribute to the project, you will have to install it with poetry. Poetry is a project management system for python. You can install poetry with pip by running `pip install poetry` on Windows, or `pip3 install poetry` on MacOS and Linux.

Next, clone the project with git by running `git clone https://github.com/kronifer/code-jam-9`. Open a shell/command prompt and move into this directory, then run `poetry install`. All of the project's required dependencies will be installed in a virtual environment. Once all the dependencies are done installing, run `poetry run pre-commit install` to install pre-commit and you'll be ready to contribute.

### Committing and Pushing Code to a New Branch

Once you've installed the project, you can activate the virtual environment by running `poetry shell`. You'll be put into a new shell with a new python interpreter which only has the dependencies listed in pyproject.toml installed.

In this shell you've opened, you need to do a few things before you start coding. First, pull the latest changes from Github by using `git pull`, and then create a new branch using `git branch {name}` or `git checkout -b {name}`. The latter will let you skip a step by automatically switching to the branch. If you went with the first command, use `git checkout {name}` to switch to the new branch. Now, you can start coding whatever you've been assigned.

Before you commit what you've coded, there are a few things you need to do. First, format your code with `poetry run task format`. After that, you'll need to sort your imports using `poetry run task sort`. After that, your code should be ready to commit and push. Did your commit fail? Run `poetry run flake8 .` to check for any formatting problems in your code. The commands you have run above should format almost everything for you, but there are some things that tools cannot fix for you that you have to fix yourself. Fix any errors that flake8 gives you and try again. If that fails, rinse and repeat until your code passes.

### Merging your Branch into Main

Once you've pushed your code and feel it's ready to be merged into the main branch, open a pull request on Github. Make sure the title of your PR makes sense and the description explains what you've done. Once your code passes the style check and has been approved by one other team member, it can be merged and you can move on to your next assignment.
