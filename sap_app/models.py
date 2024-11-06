from django.db import models
from .constants import ReturnType, ReturnReason

# Create your models here.
class ReturnSapModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    gate_pass_no=models.CharField(max_length=10,null=False)
    billing_doc_no=models.CharField(max_length=10,null=False)
    billing_date=models.DateField(null=False)
    route=models.CharField(max_length=10,null=False)
    return_type=models.CharField(max_length=10,null=False, choices=ReturnType.choices)
    return_reason=models.CharField(max_length=10,null=False, choices=ReturnReason.choices)
    
    def __str__(self):
        return f'{self.billing_doc_no}- {self.billing_date}'
    
    class Meta:
        db_table = "rdl_return_sap"
        verbose_name = "SAP Return"
        verbose_name_plural = "SAP Return"