#change port

'''
Warehouse
   │
Create Product
   │
Redis (Products)
   │
   ▼
Store receives customer order
   │
Gets product from Warehouse
   │
Calculates fee & total
   │
Creates Order
   │
Redis (Orders'''

from fastapi import FastAPI
import requests
from fastapi.middleware.cors import CORSMiddleware
from redis_om import HashModel, get_redis_connection
from fastapi.background import BackgroundTasks      #redis stream #atomatic update function
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ['http://localhost:3000','https://fastapi-store-frontend.onrender.com'],
    allow_methods =['*'],
    allow_headers =['*']
)
'''
Redis Server
│
├── DB 0 → Warehouse microservice
├── DB 1 → Store microservice
└── DB 2 → Notification microservice'''

redis = get_redis_connection(
    host ='muscle-hypersteady-truthful-39324.db.redis.io',   # In realtity we can have new database
    port = 16216,
    password='AT02xX5wMAK1zFE6kqSwcaIVxk2Ojqcd',
    decode_responses=True   # return strings instead of bytes
)

class ProductOrder(HashModel,index =True):  # send request
    product_id: str
    quantity:int
    class Meta:
        database = redis

class Order(HashModel,index =True):  # recieve request
    product_id: str
    price :float
    fee: float
    total:float
    quantity: int
    status: str
    class Meta:
        database = redis

@app.post('/orders')
def create(productOrder: ProductOrder,background_tasks: BackgroundTasks):
    req = requests.get(f'http://localhost:8000/product/{productOrder.product_id}')  #ask warehouse return below dict
    product = req.json()   #python dictionary
    fee = product['price'] * 0.2     # 20%

    order = Order(   #order object
        product_id= productOrder.product_id,
        price =product['price'],
        fee =fee,
        total = product['price'] + fee,
        quantity =productOrder.quantity,
        status='pending'
'''Order(...)
        │
        ▼
HashModel._init_(...)
        │
        ▼
Creates the object and stores:
product_id
price
fee
total
quantity
status'''
    )
    order.save()
    background_tasks.add_task(order_complete,order)  #client get response immediately while status update happens in background
    '''order_complete(order) = do it now
       order_complete + order = remember this function and these arguments; do it later'''
    return order

@app.get('/orders/{pk}')
def get(pk:str):
    return format(pk)

@app.get('/orders')
def get_all():
    return [format(pk) for pk in Order.all_pks()]

def format(pk:str):
    order =Order.get(pk)
    return{
        'id':order.pk,
        'product_id':order.product_id,
        'fee':order.fee,
        'total':order.total,
        'quantity':order.quantity,
        'status':order.status
    }


def order_complete(order: Order):
    time.sleep(5)  #pretend as payment
    order.status ='completed'
    order.save()
    redis.xadd(name='order-completed',fields = order.model_dump())  # pblishing the event redis stream

    '''Store
   │
   ▼
Redis Stream(message n th times in queue)
   │
   ├── Warehouse reads
   ├── Notification reads
   └── Invoice reads'''
 


    '''Order object (inheritance)
      │
Does Order have save()?
      │
No
      │
Check parent class (HashModel)
      │
   Found save() get() delete()
      │
Execute HashModel.save()
      │
Store the object in Redis'''
    