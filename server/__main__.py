import asyncio
import json

import websockets

from .connections import Connections
from .questions import Questions

CONNECTIONS = Connections()
QUESTIONS = Questions()


def update_scores(scores: dict, answers: dict, correct: int):
    """
    Update scores dict

    Updates a dict of player scores in place, awarding one point
    for correct answers and zero for incorrect
    """
    players = scores.keys()
    for uname, answer in answers.items():
        if uname not in players:
            raise KeyError(
                f"Answer received from {uname}, but {uname!r} is not present in scores dict"
            )
        # +1 if correct, +0 otherwise
        scores[uname] += answer == correct


async def request_uname(ws) -> str:
    """Requests a newly connected client's username."""
    await ws.send('{"event": "uname_request"}')
    uname = json.loads(await ws.recv())["uname"]
    if uname in CONNECTIONS.data.keys():
        await ws.send('{"error": "username already used"}')
        uname = await request_uname(ws)
    CONNECTIONS.add_user(uname, ws)
    return uname


async def request_user_limit(ws) -> None:
    """Requests the user limit for the game from the first user who connects."""
    await ws.send('{"event": "ulimit_request"}')
    ulimit = json.loads(await ws.recv())["ulimit"]
    if ulimit < 2 or ulimit % 1 != 0:
        await ws.send('{"error": "ulimit must be an integer greater than 1"}')
        ulimit = await request_user_limit(ws)
    CONNECTIONS.user_limit = ulimit


async def connect(ws) -> None:
    """
    Websocket connection handler.

    Prompts for a username after checking
    if more users can join, then waits to remove the user when they user_leave
    """
    try:
        if len(CONNECTIONS) >= CONNECTIONS.user_limit:
            await ws.send('{"error": "user limit has been reached"}')
            await ws.close()
            return
    # user_limit has not been assigned a value yet
    except TypeError:
        pass
    uname = await request_uname(ws)
    # This property is initialized to None, so this reliably checks if it has to be requested
    if CONNECTIONS.user_limit is None:
        await request_user_limit(ws)
    try:
        await ws.wait_closed()
    finally:
        CONNECTIONS.remove_user(uname)


async def send_event() -> None:
    """Sends events to all websockets."""
    user_count = CONNECTIONS.user_count
    if user_count != len(CONNECTIONS):
        # There should be an extra user if one has joined, and a missing
        # one if one has left
        current_users = CONNECTIONS.current_users
        event_type = "user_join" if user_count < len(CONNECTIONS) else "user_leave"
        user_count = len(CONNECTIONS)
        websockets.broadcast(
            CONNECTIONS.data.values(),
            f'{{"event": "{event_type}", "count": {user_count}, "uname_list": {current_users}}}',
        )
        CONNECTIONS.update_user_count()
    elif user_count == CONNECTIONS.user_limit and not CONNECTIONS.game_started:
        # What if user_count equals the limit and the game is started?
        await list(CONNECTIONS.data.values())[0].send('{"event": "start_request"}')
        start = bool(await list(CONNECTIONS.data.values())[0].recv())
        if start:
            websockets.broadcast(CONNECTIONS.data.values(), '{"event": "game_start"}')
            CONNECTIONS.game_started = True
    await asyncio.sleep(1)


async def send_question(question) -> None | int:
    """Sends questions to all users and return integer of correct answer."""
    if CONNECTIONS.game_started:
        send_question = question.copy()
        answer = send_question.pop("correct_answer")
        send_question = json.dumps(send_question)
        websockets.broadcast(CONNECTIONS.data.values(), send_question)
        return answer


async def collect_answers():
    """Gathers player answers to most recently asked question"""
    if CONNECTIONS.game_started:
        return {uname: await conn.recv() for uname, conn in CONNECTIONS.data.values()}


# for conn in CONNECTIONS.data.values():
# index = list(CONNECTIONS.data.values()).index(conn)
# uname = list(CONNECTIONS.data.keys())[index]
# question_choices[uname] = await conn.recv()


async def main():
    """Runs the websockets server."""
    async with websockets.serve(connect, "localhost", 8081):
        while True:
            await send_event()
            # Dict to track player scores
            scores = {uname: 0 for uname in CONNECTIONS.data.keys()}
            conns = CONNECTIONS.data.values()
            # Iterate sending a question, collecting answers, and checking them
            for question in QUESTIONS.questions:
                correct = await send_question(question)
                answers = await collect_answers()
                asyncio.sleep(1)
                update_scores(scores, answers, correct)
                websockets.broadcast(conns, "Latest scores: ")
                websockets.broadcast(conns, json.dumps(scores))

            # Sort scores in descending order
            scores = {
                uname: score
                for uname, score in sorted(scores.items(), key=lambda item: -item[1])
            }
            websockets.broadcast(conns, "Final scores: ")
            websockets.broadcast(conns, json.dumps(scores))
            # Since the first element has the highest score
            winner = next(iter(scores.keys()))
            # TODO tiebreaker method of closest to selected random number
            websockets.broadcast(conns, f"The winner is {winner}!")


if __name__ == "__main__":
    asyncio.run(main())
