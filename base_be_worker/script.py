from queue_jobs import QueueJobClient
import ujson
import time
from random import choice
from string import ascii_lowercase

s = ''.join([choice(ascii_lowercase) for _ in range(1000000)])

dict1 = ["send_sms_v2",["rgao-wish","5197293902","US","Hello there 5 kk","",""],{"_queued_time":time.time()}]
dict2 = ["send_sms_v2",["rgao-wish","5197293902","US","Hello there 6","",""],{"_queued_time":time.time()}]
large_str = "123" * 256 * 1024 * 2

dicts = [dict1, dict2]

prop = {'content_type': {'DataType': 'String', 'StringValue': 'text/plain'}}
props = [prop, prop]

kwargs = {
    'env': 'stage',
    'user_id': 'roy',
}

QueueJobClient.init(**kwargs)

client = QueueJobClient.get_queuejob_client('us-west-1', 'sweeper_sms_v2')
client.queuejob(dict1, prop)




