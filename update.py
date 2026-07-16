import time
from main import redis,Order

#x stands for stream  #redis.xadd(name='order-completed',fields = order.model_dump())
key = 'refund-order'   #one stream
group='payment'    # imagine if several servers ,consumer group

try: 
    '''Create a consumer group called warehouse-group for the stream order-completed'''
    redis.xgroup_create(name=key,groupname=group,mkstream=True)
    print('Group Created')
except Exception as e:
    print(str(e))  # print string message of error 

while True:  #keep running forever
    try:
        '''">" means give me only new messages that haven't been delivered to this consumer group yet'''
        results= redis.xreadgroup(groupname=group,consumername=key,streams={key:'>'})
        print(results)
        if results != []:
            for result in results:
                obj = result[1][0][1]  #indexing
                order= Order.get(obj['pk'])
                order.status = 'refunded'
                order.save()
                print(order)
    except Exception as e:
        print(str(e))
    time.sleep(3)