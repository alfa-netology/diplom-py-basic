import requests

from modules.logger import set_logger
logger = set_logger(__name__)

with open('.tokens/yandex') as file_object:
    token = file_object.read().strip()

class YaUploader:
    def __init__(self):
        self.token = token
        self.title = 'Yandex Disk'

    @property
    def _auth_header(self):
        """ заголовок для авторизации """
        return {'Authorization': self.token}

    def make_dir(self, dir_name):
        url = 'https://cloud-api.yandex.net:443/v1/disk/resources'
        params = {'path': dir_name}

        response = requests.put(url, headers=self._auth_header, params=params)

        if response.status_code == 201:
            logger.info(f"'{dir_name}' folder create successfully")
        else:
            error_message = response.json()['message']
            logger.error(f"<{response.status_code}> {error_message}")

    def upload(self, file_name, image_url):
        """ загруджает файл file на яндекс диск"""
        status, result = self._get_upload_link(file_name)

        if status is True:
            url = result
            image = requests.get(image_url)

            try:
                response = requests.put(url, image.content)

                if response.status_code == 201:
                    logger.info(f"'{file_name}' successfully upload to YaDisk.")
                else:
                    status_code = response.status_code
                    error_message = response.json()['message']
                    logger.error(f" <{status_code}> {error_message} filename: {file_name}")

            except Exception as e:
                logger.error(e)

        else:
            logger.error(f"{result}")

    def _get_upload_link(self, file_name):
        """ получает ссылку для загрузки """
        url = 'https://cloud-api.yandex.net:443/v1/disk/resources/upload'
        params = {'path': file_name}
        response = requests.get(url, headers=self._auth_header, params=params)

        if response.status_code == 200:
            logger.info(f"'{file_name}' link to upload successfully received")
            return True, response.json()['href']
        else:
            error_message = response.json()['message']
            return False, f"<{response.status_code}> {error_message}"
