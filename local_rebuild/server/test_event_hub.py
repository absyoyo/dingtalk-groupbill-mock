import asyncio

from local_rebuild.server.event_hub import EventHub


def test_ring_buffer_keeps_most_recent_events():
    hub = EventHub(capacity=3)
    for index in range(5):
        hub.publish({"seq": index})
    assert [event["seq"] for event in hub.recent()] == [2, 3, 4]


def test_subscribers_receive_published_events():
    hub = EventHub(capacity=10)
    received: list[dict] = []

    async def scenario():
        queue = hub.subscribe()
        hub.publish({"seq": 1})
        received.append(await asyncio.wait_for(queue.get(), timeout=1))
        hub.unsubscribe(queue)

    asyncio.run(scenario())
    assert received == [{"seq": 1}]


def test_subscriber_count_tracks_subscriptions():
    hub = EventHub(capacity=2)
    hub.subscribe()
    assert hub.subscriber_count() == 1