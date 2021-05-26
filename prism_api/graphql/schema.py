from os import path

import ariadne

from . import resolvers
from .entities.wrappers import Problem

basepath = path.dirname(__file__)
schemapath = path.abspath(path.join(basepath, 'schema'))


typedefs = ariadne.load_schema_from_path(schemapath)


problem_interface = ariadne.InterfaceType('ProblemInterface')

task_problems = ariadne.UnionType('TaskProblems')


@problem_interface.type_resolver
def resolve_problem_interface_type(obj: Problem, *_):
    return obj.resolve_type()


@task_problems.type_resolver
def resolve_validation_problem_type(obj, *_):
    return obj.resolve_type()


schema = ariadne.make_executable_schema(
    typedefs,
    resolvers.query,
    resolvers.mutation,
    resolvers.workflow_object,
    problem_interface,
    task_problems,
)
