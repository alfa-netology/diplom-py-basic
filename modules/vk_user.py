import requests
import itertools
from time import sleep
from datetime import datetime
from tqdm import tqdm
import json

import modules.colors as COLORS
from modules.logger import set_logger

logger = set_logger(__name__)

class VkUser:
    def __init__(self, token, api_version, user_id):
        self.token = token
        self.api_version = api_version
        # для проверки id на валидность
        self.id_status = False

        self.id = self._check_id(user_id)
        self.albums = self._get_albums()

    def _check_id(self, user_id):
        """
        проверяет введеный id на валидность
        в случае успешного прохождения проверок, возвращает id пользователя
        """
        add_params = {'user_ids': user_id}
        response = self._execute_requests('users.get', add_params)

        if 'error' in response:
            # проверка id на существование
            result = response['error']['error_msg']
            logger.error(f"{result} '{user_id}'")
            return result

        if response['response'][0]['is_closed'] is True and response['response'][0]['can_access_closed'] is False:
            # проверка id (открытый/закрытый)
            result = 'Private account'
            logger.error(f"{result} '{user_id}'")
            return result
        else:
            # в случае успешного прохождения проверок, возвращает id пользователя
            self.id_status = True
            result = response['response'][0]['id']
            logger.info(f"Create instance VkUser for '{user_id}' id #{result}")
            return result

    def backup(self, albums_to_backup, quantity=5):
        photos = {}
        album_size = albums_to_backup[0]['album_size']

        # маловероятный случай, но подстрахуемся
        try:
            int(quantity)
        except ValueError:
            message = f"'{quantity}' invalid attribute for backup() function"
            print(f"{COLORS.FAILURE} {message}")
            logger.error(message)
            exit()

        if quantity > album_size:
            message = f"user have only {album_size} photos, required {quantity}"
            print(f"{COLORS.FAILURE} {message}")
            logger.error(message)
            exit()

        # total backup берем все файлы
        elif quantity == 0:
            for item in tqdm(albums_to_backup, colour='#188FA7', ncols=100, desc=f"receive data for backup"):
                photos.update(self._get_all_photos(item['album_id'], item['album_title']))
        else:

        
        with open('text.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(photos, indent=4, ensure_ascii=False))

    def _get_photos(self, album_id, album_title, offset=0, result=None):
        """
        получает все фотографии из альбома album_id в максимальном разрешении,
        возвращает словарь photos[photo_id] = { album_title, название альбома
                                                date: дата загрузки с точностью до милисекунд,
                                                likes: количество лайков,
                                                size: размер фото в специальном формате vk_api,
                                                url: ссылка на фото }
        """
        params = {
            'user_id': self.id,
            'extended': 1,
            'offset': offset,
            'count': 1000,
        }

        if album_id == -9000:
            # для получения фотографий из альбома "Фото со мной"
            method = 'photos.getUserPhotos'
        else:
            # для получения фотографий из всех остальных альбомов
            method = 'photos.get'
            params = {**params, 'album_id': album_id}

        response = self._execute_requests(method, params)
        sleep(1)
        total_album_photos = response['response']['count']

        if not result:
            result = {}

        for item in response['response']['items']:
            result[item['id']] = {
                'album_title': album_title,
                'date': datetime.fromtimestamp(item['date']).strftime("%Y-%m-%d-%H%M%S%f"),
                'likes': item['likes']['count'],
                # самый большой размер последний в списке sizes
                'size': item['sizes'][-1]['type'],
                'url': item['sizes'][-1]['url'],
            }

        offset += 1000

        if offset < total_album_photos:
            self._get_photos(album_id, album_title, offset=offset, result=result)
        return result

    def _get_albums(self):
        """
        получает список всех непустых альбомов пользователя.
        альбомы Фотографии со страницы, Фотографии на стене, Сохраненные фотографии и Фотографии со мной,
        переименовываются, в соотвествии со словарем 'replace_title'.
        эти имена будут использованы при сохранении каждого альбома в свою папку.
        вовзращает словарь albums, который в дальнейшем будет использован для выбора альбомов для сохранения
        all photos - все доступные фотографии,
        user albums - все альбомы пользователя,
        service - каждый сервисный альбом можно будет сохранить по отдельности
        """
        params = {'owner_id': self.id, 'need_system': 1}
        response = self._execute_requests('photos.getAlbums', params)
        albums = {}

        owner_items = []
        # для подсчета общего числа фото в альбомах пользователя
        owner_total_size = 0
        service_items = []
        # для подсчета общего числа фото в сервисных альбомах
        service_total_size = 0

        for item in response['response']['items']:
            album_id = item['id']
            album_title = self._replace_album_title(album_id, item['title'])
            album_size = item["size"]

            if album_size > 0:
                album = {
                        'id': album_id,
                        'size': album_size,
                        'title': album_title,
                    }

                if album_id in [-6, -7, -15, -9000]:
                    service_items.append(album)
                    service_total_size += album_size
                else:
                    owner_items.append(album)
                    owner_total_size += album_size

            albums.update({
                'all photos': {
                    'items': service_items + owner_items,
                    'size': service_total_size + owner_total_size
                }})

            if len(owner_items) > 0:
                albums.update({
                    'user albums': {
                        'items': owner_items,
                        'size': owner_total_size,
                    }})

            if len(service_items) > 0:
                albums.update({
                    'service': {
                        'items': service_items,
                        'size': service_total_size
                        }})

        return albums

    @staticmethod
    def _replace_album_title(album_id, album_title):
        # переименовывает сервисные альбомы
        replace_title = {
            -6: 'profile photos',
            -7: 'photos from wall',
            -15: 'saved photos',
            -9000: 'tagged photos'
        }

        if album_id in [-6, -7, -15, -9000]:
            return replace_title[album_id]
        else:
            return album_title

    def _execute_requests(self, api_method, add_params, request_method='get'):
        """ выполнение запроса к vk-api с заданными параметрами """
        request_url = f'https://api.vk.com/method/{api_method}'
        params = {
            'access_token': self.token,
            'v': self.api_version,
        }
        params = {**params, **add_params}
        result = ''

        if request_method == 'get':
            result = requests.get(request_url, params).json()
        if request_method == 'put':
            result = requests.put(request_url, params).json()

        return result

