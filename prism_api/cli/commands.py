import click

from prism_api.talktrack import actions as talktrack_actions


@click.command()
def load_talktracks():
    talktrack_actions.load_talktracks()
    click.echo('Talktracks have been loaded')
