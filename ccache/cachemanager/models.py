'''
Models for cachemanager app are defined here.
'''
from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class BaseFile(models.Model):
    '''
    Base class for text and image files.
    '''
    owner = models.ForeignKey(User,on_delete=models.RESTRICT, related_name='cachedfiles')
    filename = models.CharField(max_length=120)
    creation_time = models.DateTimeField(auto_now_add=True)
    last_update_time = models.DateTimeField(auto_now=True)
    size = models.IntegerField()

    def get_absolute_url(self):
        '''
        Returns canonical url for the object.
        '''
        return reverse("get_file", kwargs={"filename": self.filename})

    def __str__(self):
        return self.owner.username+'/'+self.filename

class TextFile(models.Model):
    '''
    Represents stored text files (css/js) in database.
    '''
    base_file = models.OneToOneField(BaseFile, on_delete=models.CASCADE, related_name='txtdetails')
    minify = models.BooleanField(default=False)
    minification_time = models.FloatField(null=True, blank=True)
    minification_memory = models.IntegerField(null=True, blank=True)

class ImageFile(models.Model):
    '''
    Represents stored image files in database.
    '''
    base_file = models.OneToOneField(BaseFile, on_delete=models.CASCADE, related_name='imgdetails')
    convert_to_webp = models.BooleanField(default=False)
    convertion_time = models.FloatField(null=True, blank=True)
    convertion_memory = models.IntegerField(null=True, blank=True)
