from django.db import models

class ReturnType(models.TextChoices):
    v0='p','p'
    v1='f','f'
    
class ReturnReason(models.IntegerChoices):
    v0=901,'Wrong Order'
    v1=902,'Pharmacy Closed'
    v2=903,'Customer Denied to Accept'
    v3=904,'No Order'
    v4=905,'Cash Short'
    v5=906,'Delayed Delivery'
    v6=907,'Damaged Goods'
    v7=908,'Price Difference'
    v8=909,'Quantity Discrepancy'
    v9=910,'Discount Discrepancy'
    v10=911,'Order Mistakenly Created'
    v11=912,'Out of Schedule'
    v12=913,'Route Cancelled'
    v13=914,'Natural Disaster'
    v14=915,'Short Dated Material'
    v15=916,'Rate Increase'
    v16=917,'Patient No More Alive'
    v17=918,'Mistakenly Created By Depot'
    v18=919,'PQC'