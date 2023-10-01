'''
Utility classes to work with caching system.
'''
import sys
import os
import time
import pathlib
import threading
import rcssmin
import rjsmin
import magic
import redis
from PIL import Image
from memory_profiler import memory_usage
from django.utils.text import slugify
from cachemanager.models import BaseFile, ImageFile, TextFile

class FileMan:
    '''
    Responsible for working with files.
    '''
    TMP_STORAGE_PATH = "./tmp/"

    def sanitize_filename(self, filename):
        '''
        Sanitizes filename.
        '''
        filename = filename.rsplit('.', maxsplit=1)
        filename[0] = slugify(filename[0])
        filename[1] = slugify(filename[1])
        return '.'.join(filename)

    def path_exists(self, path):
        '''
        Checks if directory set in path exists or not.
        '''
        return os.path.exists(path)

    def save_file_in_tmp_path(self, file, filename):
        '''
        Saves file in temporary path.
        '''
        with open(self.TMP_STORAGE_PATH+filename, 'wb') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
            destination.seek(0)

    def minify(self, filename):
        '''
        Minifies a text file inplace.
        '''
        extension = filename.rsplit('.', maxsplit=1)[-1]
        if extension == 'css':
            with open(self.TMP_STORAGE_PATH+filename, 'rt') as old_file:
                style_str = old_file.read()
            new_style = rcssmin.cssmin(style_str)
            with open(self.TMP_STORAGE_PATH+filename, 'wt') as new_file:
                new_file.write(new_style)
            return True
        elif extension == 'js':
            with open(self.TMP_STORAGE_PATH+filename, 'rt') as old_file:
                js_str = old_file.read()
            new_js= rjsmin.jsmin(js_str)
            with open(self.TMP_STORAGE_PATH+filename, 'wt') as new_file:
                new_file.write(new_js)
            return True
        return False

    def convert_to_webp(self, filename):
        '''
        Converts image file to webp.
        '''
        if filename.rsplit('.', maxsplit=1)[-1] == 'webp':
            return False
        source = pathlib.Path(self.TMP_STORAGE_PATH+filename)
        destination = source.with_suffix('.webp')
        image = Image.open(source)
        image.save(destination, format='webp')
        #os.remove(source)
        return destination.name

    def file_exists(self, path, filename):
        '''
        Checks if a fie named filename exsits inside specified path.
        '''
        return os.path.exists(path+'/'+filename)

    def move_tmp_file_to_destination_path(self, path, tmp_filename, destination_filename):
        '''
        Moves file from temporary storage to designated storage.
        '''
        os.system(f"sudo mv {self.TMP_STORAGE_PATH+tmp_filename} {path+'/'+destination_filename}")

    def remove_tmpfile(self, filename):
        '''
        Removes file named filename from temporary storage.
        '''
        return os.remove(self.TMP_STORAGE_PATH+filename)

    @classmethod
    def store_file(cls, path, uploaded_file, minify=False, convert=False):
        '''
        Store uploaded_file in specified path.
        '''
        result = {"overwritten": False}
        filename = cls.sanitize_filename(cls, str(uploaded_file))
        if not cls.path_exists(cls, path):
            os.system(f"sudo mkdir {path}")
        tmp_filename = path.rsplit('/', maxsplit=1)[-1]+'.'+filename
        cls.save_file_in_tmp_path(cls, uploaded_file, tmp_filename)
        if minify:
            start_time = time.process_time()
            minify_profile = memory_usage(
                (cls.minify, (cls, tmp_filename)),
                max_usage=True,
                retval=True,
                max_iterations=1)
            end_time = time.process_time()
            time_spent = end_time - start_time
            result['minification'] = {
                'memory_usage': minify_profile[0]*1024*1024,
                'cpu_time': time_spent
                }
        elif convert:
            start_time = time.process_time()
            convert_profile = memory_usage(
                (cls.convert_to_webp, (cls, tmp_filename)),
                max_usage=True,
                retval=True,
                max_iterations=1)
            end_time = time.process_time()
            time_spent = end_time - start_time
            result['convertion'] = {
                'memory_usage': convert_profile[0] * 1024 * 1024,
                'cpu_time': time_spent
            }
            if convert_profile[1]:
                cls.remove_tmpfile(cls, tmp_filename)
                tmp_filename = convert_profile[1]
                filename = tmp_filename.split('.', maxsplit=1)[1]
        result['filesize'] = os.path.getsize(cls.TMP_STORAGE_PATH+tmp_filename)
        if cls.file_exists(cls, path, filename):
            result['overwritten'] = True
        cls.move_tmp_file_to_destination_path(cls, path, tmp_filename, filename)
        result['filename'] = filename
        return result

    @classmethod
    def retrieve_file(cls, path, filename):
        '''
        Returns content of the file filename in path directory as bytes.
        '''
        try:
            with open(path+filename, 'rb') as file_handler:
                file_data = file_handler.read()
        except:
            return False
        return file_data

class SingletonMeta(type):
    """
    Thread-safe implementation of Singleton.
    """

    _instance = None
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        """
        Makes changing __init__ definition in subclasses possible.
        """
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__call__(*args, **kwargs)
        return cls._instance

class BaseCacheBackend(metaclass=SingletonMeta):
    '''
    Interface class for all cache backends.
    '''
    def add_record(self, key, value):
        '''
        adds key value pair to the cached records.
        '''
        raise NotImplementedError("Not implemented by concrete cache backend in use.")

    def key_exists(self, key):
        '''
        Checks if provided key exists among cached records.
        '''
        raise NotImplementedError("Not implemented by concrete cache backend in use.")

    def get_record(self, key):
        '''
        Returns value associated with the provided key.
        '''
        raise NotImplementedError("Not implemented by concrete cache backend in use.")

    def memory_used_by_key(self, key):
        '''
        Returns memory used by a key in bytes.
        '''
        raise NotImplementedError("Not implemented by concrete cache backend in use.")

class RedisCacheBackend(BaseCacheBackend):
    '''
    Cache backend based on Redis.
    '''
    memory_config = {
        'maxmemory': 512*1024*1024,
        'maxmemory-policy': 'allkeys-lru',
    }

    def __init__(self, connection_info=None):
        if connection_info is None:
            self.redis = redis.Redis()
        else:
            self.redis = redis.Redis(host=connection_info['host'], port=connection_info['port'], db=connection_info['db'])
        for config in self.memory_config.keys():
            self.redis.config_set(config, self.memory_config[config])

    def add_record(self, key, value):
        return self.redis.set(key, value)
    def key_exists(self, key):
        return self.redis.exists(key)
    def get_record(self, key):
        return self.redis.get(key)
    def memory_used_by_key(self, key):
        return self.redis.memory_usage(key)

class CustomCacheBackend(BaseCacheBackend):
    '''
    Cache backend implemented customly.
    '''
    memory_config = {
        'maxmemory': 512*1024*1024,
    }
    _total_memory_used = 0
    _last_used_key = []
    _cache = {}
    _size_cache = {}

    def __init__(self, **kwargs):
        self.called = 0
        self._cache = {}
        self._size_cache = {}

    def clear_space(self, needed_space):
        '''
        Keeps removing records from cache based on last time they were used.
        '''
        saved_space = 0
        removed_keys = []
        for key in self._last_used_key:
            del self._cache[key]
            saved_space = saved_space + self._size_cache[key]
            self._total_memory_used = self._total_memory_used - self._size_cache[key]
            del self._size_cache[key]
            removed_keys.append(key)
            if saved_space >= needed_space:
                for removed_key in removed_keys:
                    self._last_used_key.remove(removed_key)
                return True
        for removed_key in removed_keys:
            self._last_used_key.remove(removed_key)
        return False

    def add_record(self, key, value):
        '''
        Adds key-value pair to cache records. Returns True on success and False otherwise.
        '''
        value_size = sys.getsizeof(value)
        if value_size + self._total_memory_used > self.memory_config['maxmemory'] and not self.clear_space(self._total_memory_used + value_size - self.memory_config['maxmemory']):
            return False
        self._cache[key] = value
        self._total_memory_used = self._total_memory_used + value_size
        self._last_used_key.append(key)
        self._size_cache[key] = value_size
        return True

    def key_exists(self, key):
        return key in self._cache.keys()

    def get_record(self, key):
        if not self.key_exists(key):
            return False
        if key in self._last_used_key:
            self._last_used_key.remove(key)
            self._last_used_key.append(key)
        return self._cache[key]

    def memory_used_by_key(self, key):
        if self.key_exists(key):
            return self._size_cache[key]
        else:
            return 0

class CacheMan:
    '''
    Cache manager.
    '''
    #Cache configurations
    MAX_FILE_SIZE = 2097152 #2MB
    MAX_FILE_SIZE_STR = "2 MB"
    ALLOWED_FILE_TYPES = {
        'text':
            ['css', 'js'],
        'image':
            ['jpg', 'jpeg', 'png', 'webp'],
    }
    BASE_STORAGE_PATH = "/opt/"

    #Low-level classes
    _file_manager = FileMan
    _cache_backend = RedisCacheBackend()

    def verify_file_size(self, uploaded_file):
        '''
        Checks if uploaded_file's size is less than maximum file size that is allowed.
        '''
        return uploaded_file.size < self.MAX_FILE_SIZE

    def verify_file_type(self, uploaded_file):
        '''
        Checks if uploaded_file's type is within allowed file extensions.
        '''
        mime_type = magic.from_buffer(uploaded_file.read(), mime=True).split('/')
        uploaded_file.seek(0)
        if not mime_type[0] in self.ALLOWED_FILE_TYPES:
            return False
        #TODO: Separate extension based checks from file type checks. This kind of check is prone to security risks. 
        if mime_type[1] in self.ALLOWED_FILE_TYPES[mime_type[0]] \
            or \
            str(uploaded_file).rsplit('.', maxsplit=1)[-1] in self.ALLOWED_FILE_TYPES[mime_type[0]]:
            return mime_type
        return False
    
    def generate_file_path(self, uploaded_file, owner):
        '''
        Returns absoloute path in which uploaded file should be saved
        according to configuration and uploaded_file.
        '''
        return self.BASE_STORAGE_PATH+str(owner.username)

    def add_file_record_in_database(self, file_info, owner):
        '''
        Adds or updates database record representing added file.
        '''
        try:
            base_file = BaseFile.objects.get(owner=owner, filename=file_info['filename'])
            base_file.size = file_info['filesize']
        except BaseFile.DoesNotExist:
            base_file = BaseFile.objects.create(owner=owner, filename=file_info['filename'], size=file_info['filesize'])
            if file_info['uploaded_file_type'][0] == 'text':
                txt_file = TextFile.objects.create(base_file=base_file)
            elif file_info['uploaded_file_type'][0] == 'image':
                image_file = ImageFile.objects.create(base_file=base_file)
        try:
            txt_file = base_file.txtdetails
            if 'minification' in file_info.keys():
                txt_file.minify=True
                txt_file.minification_time = file_info['minification']['cpu_time']
                txt_file.minification_memory = int(file_info['minification']['memory_usage'])
            else:
                txt_file.minify = False
                txt_file.minification_time = txt_file.minification_memory = None
            txt_file.save()
        except:
            pass
        try:
            image_file = base_file.imgdetails
            if 'convertion' in file_info.keys():
                image_file.convert_to_webp = True
                image_file.convertion_time = file_info['convertion']['cpu_time']
                image_file.convertion_memory = file_info['convertion']['memory_usage']
            else:
                image_file.convert_to_webp = False
                image_file.convertion_time = image_file.convertion_memory = None
            image_file.save()
        except:
            pass        
        return base_file

    def generate_key(self, owner_username, filename):
        return f"{owner_username}_{filename}"

    @classmethod
    def add_file_record(cls, uploaded_file, owner, minify=False, convert=False, **kwargs):
        '''
        Saves file in physical storage and creates db entry for that file.
        '''
        if not cls.verify_file_size(cls, uploaded_file):
            return {'success': False, \
                'errors': [f"Uploaded file's size should be less than {cls.MAX_FILE_SIZE_STR}."]}
        file_type = cls.verify_file_type(cls, uploaded_file)
        if not file_type:
            return {'success': False, 'errors': ["Uploaded file's type is not allowed."]}
        path = cls.generate_file_path(cls, uploaded_file, owner)
        if file_type[0] == 'text':
            convert = False
        if file_type[0] == 'image':
            minify = False
        file_storage_result = cls._file_manager.store_file(
            path,
            uploaded_file,
            minify=minify,
            convert=convert
            )
        file_storage_result.update({'uploaded_file_type': file_type})
        db_object = cls.add_file_record_in_database(cls, file_storage_result, owner)
        file_storage_result.update({'file_id': db_object.id, 'url': db_object.get_absolute_url()})
        cls.save_file_in_cache(file_storage_result['filename'], owner)
        return {'success': True, 'file_info': file_storage_result}

    @classmethod
    def save_file_in_cache(cls, filename, owner):
        '''
        Reads file content from persistant storage and saves it in cache.
        '''
        file_data = cls._file_manager.retrieve_file(cls.BASE_STORAGE_PATH+str(owner.username)+'/', filename)
        if file_data:
            if cls._cache_backend.add_record(cls.generate_key(cls, owner.username, filename), file_data):
                return file_data
        return False

    @classmethod
    def retrieve_file_from_cache(cls, filename, owner):
        '''
        Returns file content from cache. If file is not cached, first loads file in cache then returns it.
        '''
        key = cls.generate_key(cls, owner.username, filename)
        file_data = cls._cache_backend.get_record(key)
        if file_data:
            return file_data
        file_data = cls.save_file_in_cache(filename, owner)
        if file_data:
            return file_data
        return False

    @classmethod
    def file_memory_usage_in_cache(cls, filename, owner):
        '''
        Retruns memory used by filename in ram.
        '''
        key = cls.generate_key(cls, owner.username, filename)
        return cls._cache_backend.memory_used_by_key(key)

class CacheFacade:
    '''
    Clients use this class only to work with cache system.
    '''
    def __init__(self, cache_manager=CacheMan):
        self._cache_manager = cache_manager

    def store_file(self, uploaded_file, owner, minify=False, convert=False, **kwargs):
        '''
        Stores uploaded file and applies minification or convertion operation if neccessary.
        Returns result as a dictionary.
        '''
        store_result = self._cache_manager.add_file_record(
            uploaded_file,
            owner,
            minify=minify,
            convert=convert
            )
        return store_result
    def retrieve_file(self, filename, owner):
        '''
        Returns file named filename that is owned by user owner if such file exists.
        False otherwise.
        '''
        return self._cache_manager.retrieve_file_from_cache(filename, owner)

    def list_files(self, owner):
        '''
        Returns a list of files owned by owner.
        '''
        result = {
            'total_consumed_ram': 0,
            'number_of_files': 0,
            'files': []
            }
        files = owner.cachedfiles.all()
        for record in files:
            tmp_file = {}
            tmp_file['filename'] = record.filename
            tmp_file['creation_time'] = record.creation_time
            tmp_file['last_update_time'] = record.last_update_time
            tmp_file['size'] = record.size
            tmp_file['url'] = record.get_absolute_url()
            tmp_file['consumed_ram'] = self._cache_manager.file_memory_usage_in_cache(
                tmp_file['filename'],
                owner)
            result['number_of_files'] +=1
            if tmp_file['consumed_ram']:
                result['total_consumed_ram'] += tmp_file['consumed_ram']
            else:
                tmp_file['comsumed_ram'] = 0
            try:
                tmp_file['processed'] = record.txtdetails.minify
                tmp_file['type'] = "text"
                if tmp_file['processed']:
                    tmp_file['process_duration'] = record.txtdetails.minification_time
                    tmp_file['process_memory_usage'] = record.txtdetails.minification_memory
                else:
                    tmp_file['process_duration'] = tmp_file['process_memory_usage'] = 0
            except:
                pass
            try:
                tmp_file['processed'] = record.imgdetails.convert_to_webp
                tmp_file['type'] = 'image'
                if tmp_file['processed']:
                    tmp_file['process_duration'] = record.imgdetails.convertion_time
                    tmp_file['process_memory_usage'] = record.imgdetails.convertion_memory
                else:
                    tmp_file['process_duration'] = tmp_file['process_memory_usage'] = 0
            except:
                pass
            result['files'].append(tmp_file)
        return result
