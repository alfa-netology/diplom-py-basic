import requests
from time import sleep
from datetime import datetime
from tqdm import tqdm
import json
import os
import itertools

from modules.yandex_api import YaUploader
import modules.colors as colors
from modules.logger import set_logger
from modules.utils import check_dir_exists

# id сервисных альбомов
PROFILE_PHOTO = -6
WALL_PHOTO = -7
SAVE_PHOTO = -15
CHECK_USER_PHOTO = -9000
SERVICE_ALBUMS_IDS = [PROFILE_PHOTO, WALL_PHOTO, SAVE_PHOTO, CHECK_USER_PHOTO]

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
        в случае успешного прохождения проверок, возвращает id пользователя,
        в противном случае id = 'Invalid user id' или 'Private id'
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
            result = 'Private id'
            logger.error(f"{result} '{user_id}'")
            return result
        else:
            # в случае успешного прохождения проверок, возвращает id пользователя
            self.id_status = True
            result = response['response'][0]['id']
            logger.info(f"Create instance VkUser for '{user_id}' id #{result}")
            return result

    def _get_full_name(self):
        params = {'user_ids': self.id}
        response = self._execute_requests('users.get', params)
        first_name = response['response'][0]['first_name']
        last_name = response['response'][0]['last_name']
        full_name = f"{first_name} {last_name}"
        return full_name

    def backup(self, albums_to_backup, quantity=5):
        photos = {}
        album_size = albums_to_backup[0]['album_size']
        self._check_quantity(quantity, album_size)

        # выбирает все фотографии из заданных альбомов
        for item in tqdm(albums_to_backup, colour='#188FA7', ncols=100, desc=f"receive data for backup"):
            photos.update(self._get_photos(item['album_id'], item['album_title']))

        if quantity != 0:
            # выполняю условие задачи, выбрать заданое количество фото, по умолчанию пять
            # по сути костыль, но задание надо выполнять.
            photos = dict(itertools.islice(photos.items(), quantity))

        logger.info('Select photo to backup')

        self._upload_data(YaUploader(), photos)

    @staticmethod
    def _check_quantity(quantity, album_size):
        # маловероятный случай, но подстрахуемся
        try:
            int(quantity)
        except ValueError:
            message = f"'{quantity}' invalid attribute for backup() function"
            print(f"{colors.FAILURE} {message}")
            logger.error(message)
            exit()

        if quantity > album_size:
            message = f"user have only {album_size} photos in backup albums, required {quantity}"
            print(f"{colors.FAILURE} {message}")
            logger.error(message)
            exit()

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

        if album_id == CHECK_USER_PHOTO:
            # альбом 'Фото со мной' для получения фото из него у vk-api отдельный метод
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
                'date': datetime.fromtimestamp(item['date']),
                'likes': item['likes']['count'],
                # самый большой размер последний в списке sizes
                'size': item['sizes'][-1]['type'],
                'url': item['sizes'][-1]['url'],
            }

        offset += 1000

        if offset < total_album_photos:
            self._get_photos(album_id, album_title, offset=offset, result=result)
        return result

    def _upload_data(self, uploader, photos):
        root_dir = self._get_full_name()
        # уже созданные папки
        dirs_has_already = []
        # уже использованые имена файлов для сохранения
        file_names_has_already = []
        saved_files = []

        check_dir_exists('output/')
        saved_files_path = os.path.join(os.getcwd(), 'output', 'backup_result.json')
        
        uploader.make_dir(root_dir)

        for values in tqdm(photos.values(), colour='#188FA7', ncols=100, desc=f'backup data to {uploader.title}'):
            album_title = values['album_title']
            date = values['date']
            likes = values['likes']
            size = values['size']
            image_url = values['url']

            if album_title not in dirs_has_already:
                uploader.make_dir(f"{root_dir}/{album_title}")
                dirs_has_already.append(album_title)

            file_path = f"{root_dir}/{album_title}/"

            """
            имя файла как требуется по заданию:
            количество лайков дополнено ведущими 0 до 2 символов, при необходимости + дата.
            при сохранении большого количества файлов, данный формат имени файла не очень удобен,
            поэтому требуемое имя сохраняется в итоговом 'backup_result.json' как 'required name',
            а файл сохраняется с именем, которое формируется ниже как 'file_name'
            """
            required_file_name = f"{likes:02}.jpg"
            if required_file_name in file_names_has_already:
                required_file_name = f"{likes:02}_{date.strftime('%Y-%m-%d')}.jpg"
            file_names_has_already.append(required_file_name)

            """
            имя сохраняемого файла:
            кол-во лайков дополненное ведущими 0 до 4 символов + дата загрузки с точностью до милисекунд
            """
            file_name = f"{likes:04}_{date.strftime('%Y-%m-%d_%H-%M-%S-%f')}.jpg"

            uploader.upload(f"{file_path}{file_name}", image_url)

            sleep(1)

            saved_files.append({
                'target': uploader.title,
                'path': file_path,
                'name': file_name,
                'required name': required_file_name,
                'size': size
            })

        with open(saved_files_path, 'w', encoding='utf-8') as file:
            file.write(json.dumps(saved_files, indent=4, ensure_ascii=False))

    def _get_albums(self):
        """
        получает список всех непустых альбомов пользователя.
        альбомы Фотографии со страницы, Фотографии на стене, Сохраненные фотографии и Фотографии со мной,
        переименовываются _replace_album_title(), в соотвествии со словарем 'replace_title'.
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

                if album_id in SERVICE_ALBUMS_IDS:
                    service_total_size += album_size
                    service_items.append(album)
                else:
                    owner_total_size += album_size
                    owner_items.append(album)

        params = [service_items, owner_items, service_total_size, owner_total_size]
        albums.update(self._generate_result(*params))
        return albums

    # название для метода так себе, но другое не придумалось пока
    @staticmethod
    def _generate_result(service_items, owner_items, service_total_size, owner_total_size):
        service_albums = {}
        user_albums = {}

        all_albums = {'all photos': {
            'items': service_items + owner_items,
            'total_size': service_total_size + owner_total_size
        }}

        if len(owner_items) > 0:
            user_albums = {
                'user albums': {
                    'items': owner_items,
                    'total_size': owner_total_size,
                }
            }

        if len(service_items) > 0:
            service_albums = {
                'service': {
                    'items': service_items,
                    'total_size': service_total_size
                }
            }

        all_albums = {**all_albums, **user_albums, **service_albums}
        return all_albums

    @staticmethod
    def _replace_album_title(album_id, album_title):
        # переименовывает сервисные альбомы
        NAME_MAPPER = {
            PROFILE_PHOTO: 'profile photos',
            WALL_PHOTO: 'photos from wall',
            SAVE_PHOTO: 'saved photos',
            CHECK_USER_PHOTO: 'tagged photos'
        }

        return NAME_MAPPER.get(album_id, album_title)

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

