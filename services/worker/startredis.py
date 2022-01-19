import redis
import requests
import threading
from time import time, sleep
from requests.exceptions import ConnectionError
from env import get_uri


REDIS_URL = 'redis://redistogo:c1c4907a8e76ab844e2b50672864245f@sole.redistogo.com:9830/'

OPEN, CLOSED = 0, 1


def delete_reservation_worker(redis_instance):
    tag = "delete_reservation_worker"
    while True:
        if redis_instance.llen('str:delete_reservation_usernames:1') > 0:
            my_print(f"[{tag}] len of delete_reservation_usernames > 0!!!")
            username = redis_instance.lpop('str:delete_reservation_usernames:1').decode('UTF-8')

            redis_keys = list(map(bytes.decode, redis_instance.keys()))
            if not (f'str:delete_reservation_uid:{username}' in redis_keys and
                    f'str:delete_reservation_time:{username}' in redis_keys):
                redis_instance.rpush('str:delete_reservation_usernames:1', username)
                continue

            uid = redis_instance.get(f'str:delete_reservation_uid:{username}').decode('UTF-8')
            last_time = redis_instance.get(f'str:delete_reservation_time:{username}').decode('UTF-8')

            my_print(f"[{tag}] USERNAME: " + username)
            my_print(f"[{tag}] UID: " + uid)
            my_print(f"[{tag}] LAST_TIME: " + last_time)

            my_print(f"[{tag}] time passed: " + str(time() - float(last_time)))
            if time() - float(last_time) > 10:
                try:
                    my_print(f'[{tag}] Trying to execute request')
                    delete_response = requests.delete(str(get_uri('loyalty')), headers={"X-User-Name": username})
                except ConnectionError as e:
                    redis_instance.rpush('str:delete_reservation_usernames:1', username)
                    redis_instance.set(f'str:delete_reservation_time:{username}', str(time()))
                    my_print(f"[{tag}] request failed error: {e}")
                    continue
                if delete_response.status_code == 200:
                    my_print(f"[{tag}] delete loyalty request succsessful")
                else:
                    redis_instance.rpush('str:delete_reservation_usernames:1', username)
                    redis_instance.set(f'str:delete_reservation_time:{username}', str(time()))
                    my_print(f"[{tag}] request failed: {delete_response.status_code} code")
                    continue

                reservation_service_uri = get_uri('reservation')
                reservation_service_uri.path = f"reservation/{uid}"
                reservation_response = requests.get(reservation_service_uri.str)
                reservation = reservation_response.json()

                my_print(f"[{tag}] reservation get request succsessful")

                payment_service_uri = get_uri('payment')
                payment_service_uri.path = f"payment/{reservation['payment_uid']}"
                requests.patch(payment_service_uri.str, data={"status": "CANCELED"})

                my_print(f"[{tag}] payment status patch request succsessful")

                reservation_service_uri.path = f"reservation/{uid}"
                requests.patch(reservation_service_uri, data={"status": "CANCELED"})

                my_print(f"[{tag}] reservation status patch request succsessful")

                redis_instance.delete(f'str:delete_reservation_uid:{username}',
                                      f'str:delete_reservation_time:{username}')
            else:
                redis_instance.rpush('str:delete_reservation_usernames:1', username)
                sleep(1)
                my_print(f'[{tag}] Sleep 1 second because 10 seconds not less')
        else:
            sleep(1)
            my_print(f'[{tag}] Sleep 1 second because queue is empty')
            
            
def circuit_breaker_worker(redis_instance):
    tag = 'circuit_breaker_worker'
    while True:
        keys = redis_instance.keys()
        print(f'\nredis_instance.keys:\n{keys}\n\n')

        if redis_instance.llen('str:circuit_breaker_items:1') > 0:
            print(f"[{tag}] len of circuit_breaker_items > 0!!!")
            url = redis_instance.lpop('str:circuit_breaker_items:1').decode('UTF-8')

            redis_keys = list(map(bytes.decode, redis_instance.keys()))
            if not (f'int:circuit_breaker_state:{url}' in redis_keys and
                    f'str:circuit_breaker_time:{url}' in redis_keys):
                assert url != None
                redis_instance.rpush('str:circuit_breaker_items:1', url)
                continue

            state = redis_instance.get(f'int:circuit_breaker_state:{url}').decode('UTF-8')
            last_time = redis_instance.get(f'str:circuit_breaker_time:{url}').decode('UTF-8')

            print(f"[{tag}] URL: {url}")
            print(f"[{tag}] STATE: {state}")
            print(f"[{tag}] LAST_TIME: {last_time}")

            if int(state) == CLOSED:
                assert url != None
                redis_instance.rpush('str:circuit_breaker_items:1', url)
                continue

            print(f"[{tag}] time passed: " + str(time() - float(last_time)))
            if time() - float(last_time) > 5:  # TODO потом получать из редиса
                try:
                    print(f'[{tag}] Health check request')
                    response = requests.get(url)
                except ConnectionError as e:
                    assert url != None
                    redis_instance.rpush('str:circuit_breaker_items:1', url)
                    print(f"[{tag}] DEBUG Я ПОМЕНЯЛ ЛАСТ ТАЙМ при ConnectionError")
                    redis_instance.set(f'str:circuit_breaker_time:{url}', str(time()))
                    print(f"[{tag}] request failed error: {e}")
                    continue
                if response.status_code // 100 == 5:
                    assert url != None
                    redis_instance.rpush('str:circuit_breaker_items:1', url)
                    print(f"[{tag}] DEBUG Я ПОМЕНЯЛ ЛАСТ ТАЙМ при esponse.status_code // 100 == 5")
                    redis_instance.set(f'str:circuit_breaker_time:{url}', str(time()))
                    print(f"[{tag}] request failed: {response.status_code} code")
                    continue
                else:
                    redis_instance.set(f'int:circuit_breaker_state:{url}', CLOSED)
                    assert url != None
                    redis_instance.rpush('str:circuit_breaker_items:1', url)
                    print(f"[{tag}] Health check request succeeded: {response.status_code} code")
                    continue
            else:
                assert url != None
                redis_instance.rpush('str:circuit_breaker_items:1', url)
                sleep(1)
                print(f'[{tag}] Sleep 1 second because 10 seconds not less')
        else:
            sleep(1)
            print(f'[{tag}] Sleep 1 second because queue is empty')


def my_print(msg):
    print(msg)
    # block_tags = ["delete_reservation_worker"]
    # tag_search = re.search(r'\[\w*', msg)
    # tag = tag_search.group()
    # if tag[1:-1] in block_tags:
    #     return
    # else:
    #     print(msg)


if __name__ == '__main__':
    redis_conn = redis.from_url(REDIS_URL)
    redis_conn .flushdb()
    print("REDIS STARTED")

    th1 = threading.Thread(target=delete_reservation_worker, args=(redis_conn,))
    th2 = threading.Thread(target=circuit_breaker_worker, args=(redis_conn,))

    th1.start()
    th2.start()
    th1.join()
    th2.join()
