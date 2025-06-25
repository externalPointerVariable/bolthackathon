# Bolt Hackathon
## Step by step guide to get the backend server runing locally
1. Clone the `git` repository
    ```bash
    git clone https://github.com/externalPointerVariable/bolthackathon.git
    ```
2.  Install `uv` package manager in your windows machine
    ```shell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
3. Go to the directory where you have cloned the `git` repository
    ```bash
    cd bolthackathon
    ```
4. Once you are in the `git` directory run the following commands:
    ```python
    uv venv
    .venv/bin/activate
    uv pip install -r requirements.txt 
    ```
5. Once you do all this step, now you can start the server
    ```python
    cd app
    uv run manage.py runserver
    ```