<!--
SPDX-FileCopyrightText: 2025 DB Systel GmbH

SPDX-License-Identifier: Apache-2.0
-->

# Authentik User Manager

![OpenRail Administrative Project](https://openrailassociation.org/badges/openrail-project-admin.svg)
[![Test suites](https://github.com/OpenRailAssociation/authentik-user-manager/actions/workflows/test.yaml/badge.svg)](https://github.com/OpenRailAssociation/authentik-user-manager/actions/workflows/test.yaml)
[![REUSE status](https://api.reuse.software/badge/github.com/OpenRailAssociation/authentik-user-manager)](https://api.reuse.software/info/github.com/OpenRailAssociation/authentik-user-manager)
[![The latest version can be found on PyPI.](https://img.shields.io/pypi/v/authentik-user-manager.svg)](https://pypi.org/project/authentik-user-manager/)
[![Information on supported Python versions.](https://img.shields.io/pypi/pyversions/authentik-user-manager.svg)](https://pypi.org/project/authentik-user-manager/)

Manage Authentik users and group memberships via YAML configuration files.

## Features

- Synchronize users and group memberships with Authentik instance
- Configure users and their group memberships via YAML files
- Create individual invitation links for new users
- Email notification system for user invitations

## Installation

### Install and run via pipx (Recommended)

[pipx](https://pypa.github.io/pipx/) makes installing and running Python programs easier and avoids conflicts with other packages. Install it with:

```sh
pip3 install pipx
```

The following one-liner both installs and runs this program from [PyPI](https://pypi.org/project/authentik-user-manager/):

```sh
pipx run authentik-user-manager
```

If you want to use authentik-user-manager without prepending it with `pipx run` every time, install it globally:

```sh
pipx install authentik-user-manager
```

To upgrade authentik-user-manager to the newest available version:

```sh
pipx upgrade authentik-user-manager
```

### Other installation methods

You may also use pip directly:

```bash
pip install authentik-user-manager
```

## CLI Usage

authentik-user-manager provides a command-line interface for synchronizing users and their group memberships with an Authentik instance.

### Command Structure

```sh
auth-user-mgr <command> [options]
```

### Main Commands

#### sync

Synchronize users with the Authentik instance:

```sh
auth-user-mgr sync -c <config_file> -u <users_file_or_directory>
```

For detailed help on any command with additional flags such as `--dry` and `--no-email`:

```bash
auth-user-mgr --help
auth-user-mgr sync --help
```

### Configuration

The application's configuration and the list of managed users are stored in YAML files. You can find sample configuration files in the [`config/`](./config/) directory.

Note: There are two ways how to store your users inventory:

1. In a single file, as shown in [`config/users.sample.yaml`](./config/users.sample.yaml)
1. In multiple files in one directory, as shown in [`config/users.sample/`](./config/users.sample/)

#### API permissions

Especially for automated syncs, it is recommended to set up a system user in Authentik and create an API token for them. The following permissions are required:

- User: Can view User
- Group: Can view Group
- Group: Add user to group
- Group: Remove user from group
- Group: Can add Group
- Flow: Can view Flow
- Invitation: Can view Invitation
- Invitation: Can add Invitation
- Invitation: Can delete Invitation


## Development and Contribution

We welcome contributions to improve this library. Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for all information.


## License

The content of this repository is licensed under the [Apache 2.0 license](https://www.apache.org/licenses/LICENSE-2.0).

There may be components under different, but compatible licenses or from different copyright holders. The project is REUSE compliant which makes these portions transparent. You will find all used licenses in the LICENSES directory.

The project has been started by the [OpenRail Association](https://openrailassociation.org). You are welcome to contribute!
