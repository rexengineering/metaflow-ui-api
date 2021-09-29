import unittest
from asyncio.exceptions import TimeoutError

import pytest

from .utils import run_async
from rexflow_ui.events.manager.queue import EventManager
from rexflow_ui.events.errors import NotListeningError
from rexflow_ui.events.entities import Event


@pytest.mark.ci
class TestEvents(unittest.TestCase):
    def tearDown(self) -> None:
        EventManager.managers = {}  # Clear dangling listeners

    @run_async  # Needs to run in a loop or the Queue crashes
    async def test_stop_listening(self):
        self.assertEqual(0, len(EventManager.managers))
        EventManager.start_listening('one')
        self.assertEqual(1, len(EventManager.managers))
        EventManager.start_listening('two')
        self.assertEqual(2, len(EventManager.managers))
        EventManager.stop_listening('one')
        self.assertEqual(1, len(EventManager.managers))
        EventManager.stop_listening('two')
        self.assertEqual(0, len(EventManager.managers))

    @run_async
    async def test_event_queue(self):
        listener = EventManager.start_listening()

        EventManager.dispatch(Event.START_BROADCAST)
        wrapper = await listener.get()
        self.assertEqual(wrapper.event, Event.START_BROADCAST)

        EventManager.dispatch(Event.START_TASK)
        EventManager.dispatch(Event.UPDATE_TASK)
        EventManager.dispatch(Event.FINISH_TASK)

        manager = EventManager.get_manager()
        wrapper = await manager.get(timeout=1)
        self.assertEqual(wrapper.event, Event.START_TASK)
        wrapper = await manager.get(timeout=1)
        self.assertEqual(wrapper.event, Event.UPDATE_TASK)
        wrapper = await manager.get(timeout=1)
        self.assertEqual(wrapper.event, Event.FINISH_TASK)

    @run_async
    async def test_empty_queue(self):
        listener = EventManager.start_listening()
        with self.assertRaises(TimeoutError):
            await listener.get(timeout=1)

    @run_async
    async def test_no_listener(self):
        EventManager.dispatch(Event.START_BROADCAST)

        print('test')
        with self.assertRaises(NotListeningError):
            EventManager.get_manager()

        listener = EventManager.start_listening()
        EventManager.dispatch(Event.START_WORKFLOW)
        wrapper = await listener.get(timeout=1)
        self.assertEqual(wrapper.event, Event.START_WORKFLOW)
        EventManager.stop_listening()

        EventManager.dispatch(Event.FINISH_BROADCAST)
        with self.assertRaises(TimeoutError):
            await listener.get(timeout=1)

    @run_async
    async def test_multiple_listeners(self):
        listener1 = EventManager.start_listening('test1')
        listener2 = EventManager.start_listening('test2')

        EventManager.dispatch(Event.START_TASK)

        wrapper1 = await listener1.get(timeout=1)
        self.assertEqual(wrapper1.event, Event.START_TASK)
        wrapper2 = await listener2.get(timeout=1)
        self.assertEqual(wrapper2.event, Event.START_TASK)
