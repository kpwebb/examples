# Restate Chatbot example - Python

This example shows a subset of a LLM chatbot and task runner with Restate.

Restate is a system for easily building resilient applications using **distributed durable building blocks**.

❓ Learn more about Restate from the [Restate documentation](https://docs.restate.dev).

## Running the example

To set up the example, use the following sequence of commands.

Setup the virtual env:

```shell
python3 -m venv .venv
source .venv/bin/activate
```

Install the requirements:

```shell
pip install -r requirements.txt
```

Start the app as follows:

```shell
python3 -m hypercorn chatbot/app:app
```

Start the Restate Server ([other options here](https://docs.restate.dev/develop/local_dev)):

```shell
restate-server
```

Register the service:

```shell
restate dp register http://localhost:8000
```
