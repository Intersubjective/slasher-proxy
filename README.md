


# Slasher-proxy
An experimental proxy for Alchemy-style RPC sendRawTransaction calls.


  * [Installation](#installation)
  * [Package](#package)
  * [Docker](#docker)
  * [Release](#release)
  * [GitHub Actions](#github-actions)
    + [Web service](#web-service)
  * [Act](#act)


## Table of Contents

- [slasher-proxy](#slasher-proxy)
  - [Table of Contents](#table-of-contents)
  - [Postgres LISTEN/NOTIFY mechanism](#postgres-listennotify-mechanism)
  - [Configuration settings](#configuration-settings)
    - [Notification trigger](#notification-trigger) 
    - [Debugging the LISTEN/NOTIFY connection](#debugging-the-listennotify-connection)
  - [Prerequisites](#prerequisites)
    - [Development](#development)
    - [Deployment](#deployment)
  - [Development](#development-1)
    - [Step 1: Update and Install Dependencies](#step-1-update-and-install-dependencies)
    - [Step 2: Install Pyenv](#step-2-install-pyenv)
    - [Step 3: Install Python 3.12](#step-3-install-python-312)
    - [Step 4: Connect Poetry to it](#step-4-connect-poetry-to-it)
  - [Docker](#docker)
  - [Package](#package)
  - [Release](#release)
  - [GitHub Actions](#github-actions)
    - [Web service](#web-service)
  - [Act](#act)

## Configuration settings
The Proxy uses BaseSettings package from Pydantic, meaning that it will gather 
the settings from (lower number has higher priority):
1. Environment variables
2. `.env` file located in the app dir
3. Custom-provided environment variables file (when running in the CLI mode)

Pydantic verifies the correctness of the provided values. The typical `.env` file should look like:
```env
RPC_URL="http://localhost.localhost"
DSN="postgresql://slasher_user:somepassword@localhost:5432/slasher_db"
BLOCKS_CHANNEL="new_block"
LOG_LEVEL="DEBUG"
```
* `RPC_URL` (required) should point to the actual node RPC  (e.g. modified Avalanche node RPC)
* `DSN` (required) is the connection URL to the Postgre database to store the blocks, commitments, and transactions 
* `BLOCKS_CHANNEL` (required) the name of the LISTEN/NOTIFY channel over which Postgres will notify the Proxy about new blocks
* `LOG_LEVEL`(optional) - says for itself

## Postgres LISTEN/NOTIFY mechanism
Slasher-proxy receives notifications about new blocks from Postgres through LISTEN/NOTIFY mechanism.
The mechanism uses a named notification channel. You will have to provide the name 
of the channel as a configuration parameter `BLOCKS_CHANNEL`.
### Notification trigger
You will have to add a custom notification trigger to the Postgres DB:
```sql
CREATE OR REPLACE FUNCTION notify_new_block()
RETURNS TRIGGER AS $$
BEGIN
    -- Send a NOTIFY with the index of the new block
    PERFORM pg_notify('new_block', NEW.number::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_notify_new_block
AFTER INSERT ON block
FOR EACH ROW
EXECUTE FUNCTION notify_new_block();
```
This will create a trigger for the channel named `new_block` on the table named `block`,
sending the `number` field as text to the Proxy.


### Debugging the LISTEN/NOTIFY connection
A useful Postgres snippet for debugging the connection is:
```sql
SELECT
    a.pid,
    a.usename AS user,
    a.application_name,
    a.client_addr AS client_address,
    a.client_port,
    array_agg(l.channel) AS channels
FROM
    pg_stat_activity a
LEFT JOIN LATERAL
    (SELECT pg_listening_channels() AS channel) l
    ON true
WHERE
    l.channel IS NOT NULL
GROUP BY
    a.pid, a.usename, a.application_name, a.client_addr, a.client_port;
```
It will show all the connected users and channels they listen to, something like
```ascii
  pid   |     user     | application_name | client_address | client_port |  channels   
--------+--------------+------------------+----------------+-------------+-------------
 170300 | slasher_user |                  | 127.0.0.1      |       49856 | {new_block}

```

  

## Prerequisites
### Development
  - [Python 3.12](#step-2-install-pyenv) - look at detailed instructions below
  - [pipx](https://pipx.pypa.io/stable/)
  - [poetry](https://python-poetry.org/docs/)
  - [docker](https://docs.docker.com/get-docker/)
  - [Act](#act)

### Deployment
  - [Github Actions](#github-actions) - repository use Github Actions to automate the build, test, release and deployment processes. For your convinience we recommend to fill necessary secrets in the repository settings.


## Development
<details>
<h4><summary>Install Python 3.12 if it is not available in your package manager</summary></h4>

These instructions are for Ubuntu 22.04 and may not work for other versions.

Also, these instructions are about using Poetry with Pyenv-managed (non-system) Python.
 
### Step 1: Update and Install Dependencies
Before we install pyenv, we need to update our package lists for upgrades and new package installations. We also need to install dependencies for pyenv. 

Open your terminal and type:  
```bash
sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils \
tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

### Step 2: Install Pyenv
We will clone pyenv from the official GitHub repository and add it to our system path.
```bash
git clone https://github.com/pyenv/pyenv.git ~/.pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
exec "$SHELL"
```
For additional information visit official [docs](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation)

### Step 3: Install Python 3.12
Now that pyenv is installed, we can install different Python versions. To install Python 3.12, use the following command:
```bash
pyenv install 3.12
```

### Step 4: Connect Poetry to it
Do this in the template dir. Pycharm will automatically connect to it later
```bash
poetry env use ~/.pyenv/versions/3.12.1/bin/python
```
(change the version number accordingly to what is installed)

Finally, verify that Poetry indeed is connected to the proper version:
```bash
poetry enf info
```
</details>  


1. If you don't have `Poetry` installed run:
```bash
pipx install poetry
```

2. Install dependencies:
```bash
poetry config virtualenvs.in-project true
poetry install --no-root --with dev,test
```

3. Install `pre-commit` hooks:
```bash
poetry run pre-commit install
```

4. Launch the project:
```bash
poetry run uvicorn slasher_proxy.main:app 
```
or do it in two steps:
```bash
poetry shell
uvicorn slasher_proxy.main:app
```

alternatively, use the direct CLI call form:
```bash
poetry shell
env PYTHONPATH=./ python slasher_proxy/main.py avalanche
```

5. Running tests:
```bash
poetry run pytest
```

You can test the application for multiple versions of Python. To do this, you need to install the required Python versions on your operating system, specify these versions in the `tox.ini` file, and then run the tests:
```bash
poetry run tox
```


## Docker
Build a [Docker](https://docs.docker.com/) image and run a container:
```bash
docker build . -t <image_name>:<image_tag>
docker run <image_name>:<image_tag>
```

Upload the Docker image to the repository:
```bash
docker login -u <username>
docker push <image_name>:<image_tag>
```




## Release
To create a release, add a tag in GIT with the format a.a.a, where 'a' is an integer.
```bash
git tag 0.1.0
git push origin 0.1.0
```
The release version for branches, pull requests, and other tags will be generated based on the last tag of the form a.a.a.

## GitHub Actions
[GitHub Actions](https://docs.github.com/en/actions) triggers testing, builds, and application publishing for each release.  

### Web service
The default build and publish process is configured for a web application (`.github\workflows\build_web.yaml`).

**After execution**  
The Docker image will be available at `https://github.com/orgs/<workspace>/packages?repo_name=<project>`.

**Initial setup**  
Set up a [secret token](https://pypi.org/help/#apitoken) for PyPI at `https://github.com/<workspace>/<project>/settings/secrets/actions`.

**After execution**  
A package will be available at `https://github.com/<workspace>/<project>/releases/` and pypi.org. 

## Act
[Act](https://github.com/nektos/act) allows you to run your GitHub Actions locally (e.g., for developing tests)

Usage example:
```bash
act push -j deploy --secret-file my.secrets
```
