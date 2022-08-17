# Kindly Kappa

Have you had trouble learning about debugging in python? Do you perhaps just want a continuous challenge? Then look no further!

This game provides a fun and interactive environment to learn more about the dubugging process by _slowly_ introducing bugs into the code you write. By doing this, we give you the chance to become more familiar with common python errors earlier so you are well equipped for future projects. We have several different types of bugs that we introduce to cause specific errors.

## Syntax Errors

- Colons are removed from if statements, for and while loops, and type annotations.
- Python keywords are changed at random.
- Equality operators are replaced with assignments.
- Brackets (`()[]`) are randomly added or removed.

## Indentation Errors

- Indentation is de-indented by two spaces.
- Insertion of empty if statements.

## Others

- Lines of code are commented out.
- Function names when called are replaced.
- Logical errors are introduced by mixing up booleans.
- Type keywords, such as `int` or `bool`, are mixed up.

We introduce difficulty levels for the more experienced who want to challenge themselves by increasing the frequency of bugs introduced. The difficulty also scales based on the amount of code that is written in the editor. As an added feature, regardless of the level you choose, the timer may malfunction and your cursor may also reset back to the start of the editor.

| Level | Frequency (s) |
| :---: | :-----------: |
|   1   |      60       |
|   2   |      45       |
|   3   |      30       |

# Installation

## Backend

The backend was made using [fastapi](https://fastapi.tiangolo.com/) and [starlette](https://www.starlette.io/). To get started:

1. Clone the repository (or you can also download it as a .zip and extract it if you don't have git installed):
   `git clone https://github.com/Vthechamp22/kindly-kappa.git`
2. Install the dependencies (using a [virtual environment](https://realpython.com/python-virtual-environments-a-primer/) is recommended):
   `pip install -r requirements.txt`
3. Start the backend by opening a terminal in the root folder, and then running
   `uvicorn server.main:app`
   If you want to test the backend, you can create a dummy frontend by running
   `python -m websockets ws://localhost:8000/room`
4. We have also used [snekbox](https://github.com/python-discord/snekbox) to handle the evaluation of code. To start it up, first make sure you have [docker](https://www.docker.com/) installed. Then run
   `docker run --ipc=none --privileged -p 8060:8060 ghcr.io/python-discord/snekbox`
   > NOTE: You might need to run this command with `sudo`

The backend is now up and running!

## Frontend

The frontend for this project was made using Vite and Vue. In order to run it, you need to first install node. This project has been tested with v16.16.0, v17.2 and v18.6.0

1.  - Windows: Go to [nodejs.org](https://nodejs.org) and install the latest LTS version of node. (≥ 16.16.0)
    - Linux:
      1.  You can use a node version manager like [fnm](https://github.com/Schniz/fnm) or [nvm](https://github.com/nvm-sh/nvm)
      2.  Use it to install the latest LTS version (`fnm install --lts` or `nvm install --lts`)
2.  Spin up a new shell and move into the `frontend` folder.
3.  Install all the dependencies by running
    `npm install`
4.  Run the project by running
    `npm run dev`
