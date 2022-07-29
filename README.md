# Dynamic Dryads

This is our submission to Python Discord's ninth code jam. This README will be updated as needed.

To contribute, view our [contributing guide](CONTRIBUTING.md).

## How To Play With Multiple People

We suggest utilizing `ngrok` to play online with multiple people. Start the server by running `poetry install` to install the project, and then `poetry run python -m server` to start the server. Then, sign up for a free ngrok account at https://ngrok.io and install the `ngrok` CLI using the site's instructions. Once ngrok is set up, you can use it to make the server available everywhere by running `ngrok tcp 8081` and sharing the forwarding link with friends.

To run the client locally, you must have `node` installed. Then, navigate to the client directory with  `cd ./client`, and install dependencies with `npm install`. The client can then be launched with `npm start`, which will make the client available on `localhost:8080`.
