# -*- coding: utf-8 -*-
# :Project:  metapensiero.asyncio.transaction -- tests
# :Created:    mar 15 dic 2015 15:16:56 CET
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
#

import asyncio

import pytest

from metapensiero.asyncio import transaction

@pytest.mark.asyncio
@asyncio.coroutine
def test_transaction_per_task(event_loop):

    tasks_ids = set()
    results = []

    @asyncio.coroutine
    def stashed_coro():
        nonlocal results
        results.append('called stashed_coro')

    def non_coro_func():
        tran = transaction.get(loop=event_loop)
        c = stashed_coro()
        tran.add(c)

    @asyncio.coroutine
    def external_coro():
        nonlocal tasks_ids
        task = asyncio.Task.current_task(loop=event_loop)
        tasks_ids.add(id(task))
        tran = transaction.begin(loop=event_loop)
        # in py3.5
        # async with tran:
        #     non_coro_func()
        non_coro_func()
        yield from tran.end()


    yield from asyncio.gather(
        external_coro(),
        external_coro(),
        loop=event_loop
    )

    assert len(tasks_ids) == 2
    assert len(results) == 2
    assert results == ['called stashed_coro', 'called stashed_coro']

@pytest.mark.asyncio
@asyncio.coroutine
def test_non_closed_transaction(event_loop):

    tasks_ids = set()
    results = []

    event_loop.set_debug(True)

    @asyncio.coroutine
    def stashed_coro():
        nonlocal results
        results.append('called stashed_coro')

    def non_coro_func():
        tran = transaction.get(loop=event_loop)
        c = stashed_coro()
        tran.add(c)

    @asyncio.coroutine
    def external_coro():
        nonlocal tasks_ids
        task = asyncio.Task.current_task(loop=event_loop)
        tasks_ids.add(id(task))
        tran = transaction.begin(loop=event_loop)
        # in py3.5
        # async with tran:
        #     non_coro_func()
        non_coro_func()


    yield from external_coro()
    done, pending = yield from transaction.wait_all()
    # the raise from the callback gets sucked up, this is the only
    # crumb left
    assert len(done) == 1
    assert len(pending) == 0