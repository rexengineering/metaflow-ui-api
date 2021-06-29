import click

from prism_api.cli.commands import load_talktracks


@click.group()
def main():
    pass


main.add_command(load_talktracks)


if __name__ == '__main__':
    main()
