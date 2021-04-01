"""Interface to interact with REXFlow"""
from .entities import Form


class Task:
    def get_form(self) -> Form:
        # TODO
        return Form(
            fields=[
                {'question': 'testing'}
            ]
        )

    def save_form(self, form: Form) -> None:
        ...

    def complete(self) -> None:
        ...


class Workflow:
    def __init__(self):
        ...

    def finish(self):
        ...

    def get_task(self) -> Task:  # always the current task?
        # TODO
        return Task()


def get_workflow(context: dict) -> Workflow:
    # TODO
    return Workflow()
