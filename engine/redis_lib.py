import redis

RDB = redis.StrictRedis(host='localhost',
                        port=6379,
                        db=0,
                        charset="utf-8",
                        decode_responses=True)
