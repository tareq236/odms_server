from django.db import models
from .constants import ReturnType, ReturnReason

# Create your models here.
class ReturnSapModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    gate_pass_no=models.CharField(max_length=10,null=False)
    billing_doc_no=models.CharField(max_length=10,null=False)
    billing_date=models.DateField(null=False)
    route=models.CharField(max_length=10,null=False)
    return_type=models.CharField(max_length=1,null=False, choices=ReturnType.choices)
    return_reason=models.IntegerField(null=False, choices=ReturnReason.choices)
    da_code=models.CharField(max_length=10,null=False)
    sales_product_quantity=models.IntegerField(null=False)
    return_product_quantity=models.IntegerField(null=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.billing_doc_no}- {self.billing_date}'
    
    class Meta:
        db_table = "rdl_return_sap"
        verbose_name = "SAP Return"
        verbose_name_plural = "SAP Return"
        
        
class ReturnListSAPModel(models.Model):
    id=models.BigAutoField(primary_key=True)
    matnr=models.CharField(max_length=10,null=False)
    batch=models.CharField(max_length=10,null=False)
    sales_quantity=models.IntegerField(null=False)
    return_quantity=models.IntegerField(null=False)
    return_amount=models.DecimalField(null=False, max_digits=12, decimal_places=2)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    return_id=models.ForeignKey(ReturnSapModel, on_delete=models.PROTECT)
    
  
    def __str__(self):
        return f'{self.matnr}- {self.batch}'
    
    class Meta:
        db_table = "rdl_return_list_sap"
        verbose_name = "SAP Return List"
        verbose_name_plural = "SAP Return List"