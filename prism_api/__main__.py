import click

from prism_api.cli.commands import (
    cancel_workflows,
    refresh_workflows,
)


@click.group()
def main():
    pass


main.add_command(cancel_workflows)
main.add_command(refresh_workflows)


if __name__ == '__main__':
    main()
