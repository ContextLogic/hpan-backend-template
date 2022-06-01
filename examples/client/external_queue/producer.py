from base_be_worker.queue_jobs import QueueJobClient
import time
from random import choice
from string import ascii_lowercase


large_string = ''.join([choice(ascii_lowercase) for _ in range(1000000)])

dict1 = ["send_sms_v2",["rgao-wish","5197293902","US","Hello there 5 kk","",""],{"_queued_time":time.time()}]
dict2 = ["send_sms_v2",["rgao-wish","5197293902","US","Hello there 6","",""],{"_queued_time":time.time()}]

dicts = [dict1, dict2]

prop = {'content_type': {'DataType': 'String', 'StringValue': 'text/plain'}}
props = [prop, prop]


""" test case 1: successfully queue one job
kwargs = {'env': 'stage', 'user_id': 'roy'}
QueueJobClient.init(**kwargs)
client1 = QueueJobClient.get_queuejob_client('us-west-1', 'sweeper_sms_v2')
client1.queuejob(dict1, prop)
"""

""" test case 2: successfully queue multiple jobs
kwargs = {'env': 'stage', 'user_id': 'roy'}
QueueJobClient.init(**kwargs)
client1 = QueueJobClient.get_queuejob_client('us-west-1', 'sweeper_sms_v2')
client1.queuejobs(dicts, props)
"""


""" test case 3: no config kwargs, fail to init QueueJobClient due to no such queue exist, fail to queue jobs due to not ready
kwargs = {}
QueueJobClient.init(**kwargs)
client1 = QueueJobClient.get_queuejob_client('us-west-1', 'sweeper_sms_v2')
client1.queuejob(dict1, prop)

"""

""" test case 4: fix the error in case 2 by overwriting env and user id
kwargs = {}
QueueJobClient.init(**kwargs)
client1 = QueueJobClient.get_queuejob_client('us-west-1', 'sweeper_sms_v2', 'stage', 'roy')
client1.queuejob(dict2, prop)
"""

""" test case 5: job size over limit
kwargs = {'env': 'stage', 'user_id': 'roy'}
QueueJobClient.init(**kwargs)
client1 = QueueJobClient.get_queuejob_client('us-west-1', 'sweeper_sms_v2')
client1.queuejob(large_string, prop)

"""








