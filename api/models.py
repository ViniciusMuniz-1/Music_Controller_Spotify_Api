from django.db import models
import string
import random

def generate_unique_code():     #FUNÇÃO QUE GERA CÓDIGOS ALEATÓRIOS ATÉ ENCONTRAR UM QUE NÃO ESTEJA NA BASE DE DADOS
    length = 6
    
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=length))
        if Room.objects.filter(code=code).count == 0:
            break

    return code

class Room(models.Model):
    code = models.CharField(max_length=8, default=generate_unique_code, unique=True)
    host = models.CharField(max_length=50, unique=True)
    guest_can_pause = models.BooleanField(null=False, default=False)
    votes_to_skip = models.IntegerField(null=False, default=2)
    created_at = models.DateTimeField(auto_now_add=True)

    