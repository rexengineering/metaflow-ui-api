from os import path

import ariadne

from .resolvers import (
    SessionMutations,
    TalkTrackResolver,
    WorkflowMutations,
    WorkflowResolver,
    resolve_problem_interface_type,
    resolve_session,
    resolve_workflow_tasks,
)
from .subscriptions import (
    broadcast_event_subscription,
    event_generator,
    keep_alive_subscription_mutation,
)


basepath = path.dirname(__file__)
schemapath = path.abspath(path.join(basepath, 'schema'))

typedefs = ariadne.load_schema_from_path(schemapath)


query = ariadne.QueryType()
query.set_field('session', resolve_session)
query.set_field('workflows', WorkflowResolver)
query.set_field('talktracks', TalkTrackResolver)

mutation = ariadne.MutationType()
mutation.set_field('session', SessionMutations)
mutation.set_field('workflow', WorkflowMutations)

subscription = ariadne.SubscriptionType()
subscription.set_source('eventBroadcast', event_generator)
subscription.set_field('eventBroadcast', broadcast_event_subscription)
mutation.set_field('keepAlive', keep_alive_subscription_mutation)

workflow_object = ariadne.ObjectType('Workflow')
workflow_object.set_field('tasks', resolve_workflow_tasks)


problem_interface = ariadne.InterfaceType(
    'ProblemInterface',
    resolve_problem_interface_type,
)

update_state_problems_union = ariadne.UnionType(
    'UpdateStateProblems',
    resolve_problem_interface_type,
)

task_problems_union = ariadne.UnionType(
    'TaskProblems',
    resolve_problem_interface_type,
)

session_problems_union = ariadne.UnionType(
    'SessionProblems',
    resolve_problem_interface_type,
)

workflow_problems_union = ariadne.UnionType(
    'WorkflowProblems',
    resolve_problem_interface_type,
)


schema = ariadne.make_executable_schema(
    typedefs,
    # object resolvers
    query,
    mutation,
    subscription,
    workflow_object,
    # error resolvers
    problem_interface,
    update_state_problems_union,
    task_problems_union,
    session_problems_union,
    workflow_problems_union,
    # fallback resolver
    ariadne.snake_case_fallback_resolvers,
)
