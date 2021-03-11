import requests
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
        owner_total_size = 0
        service_items = []
        service_total_size = 0

        # названия для переименовывания сервисных альбомов
        replace_title = {
            -6: 'profile photos',
            -7: 'photos from wall',
            -15: 'saved photos',
            -9000: 'tagged photos'
        }

        for item in response['response']['items']:
            album_id = item['id']
            album_title = item['title']
            album_size = item["size"]

            if album_size > 0:
                item = {
                        'id': album_id,
                        'size': album_size,
                    }

                if album_id in [-6, -7, -15, -9000]:
                    # переименовываю серивисные альбомы
                    item = {**item, 'title': replace_title[album_id]}
                    service_items.append(item)
                    service_total_size += album_size
                else:
                    item = {**item, 'title': album_title}
                    owner_items.append(item)
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

