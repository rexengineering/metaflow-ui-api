import asyncio
import click

from prism_api import settings
from rexflow_ui import api as rexflow


async def _a_cancel_workflows():
    click.echo('Refreshing workflows')
    await rexflow.refresh_workflows()
    click.echo('Canceling running workflows')
    running_workflows = await rexflow.get_active_workflows()
    count = 0
    for workflow in running_workflows:
        click.echo(f'Canceling workflow {workflow.iid}')
        await rexflow.cancel_workflow(workflow.iid)
        count = count + 1

    click.echo(f'{count} workflows canceled')


@click.command()
def cancel_workflows():
    if settings.DEBUG:
        asyncio.run(_a_cancel_workflows())
    else:
        click.echo('This command can only be executed on debug mode')


async def _a_refresh_workflows():
    click.echo('Refreshing workflows')
    await rexflow.refresh_workflows()
    running_workflows = await rexflow.get_active_workflows()
    click.echo(str(running_workflows))


@click.command()
def refresh_workflows():
    if settings.DEBUG:
        asyncio.run(_a_refresh_workflows())
    else:
        click.echo('This command can only be executed on debug mode')
