from modules.vk_user import VkUser
from modules.logger import set_logger
import modules.colors as COLORS

logger = set_logger(__name__)

with open('.tokens/vk_api') as file:
    vk_access_token = file.read().strip()
vk_api_version = '5.130'

logger.info('START script')
print("VK-Photos-Backup <version 0.1>\n\n"
      "To make a backup copy photos from the vk.com account, \n"
      "enter user id or screen name (account must exist and be open).\n")

while True:
    user = input("user id: ")
    if user == '':
        print(f"\n{COLORS.FAILURE} value should not be empty. let's try again")
    else:
        break

vk_client = VkUser(vk_access_token, vk_api_version, user)

if vk_client.id_status is True:
    print(f"{COLORS.SUCCESS} '{user}' valid user id\n")
else:
    print(f"{COLORS.FAILURE} '{user}' {vk_client.id.lower()}")

logger.info('FINISH script')