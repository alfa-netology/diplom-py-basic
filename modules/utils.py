def select_albums_to_backup(albums):
    """
    формирует меню для выбора альбомов для сохранения
    возвращает словарь с индетификаторами и названиями альбомов для сохранения
    """
    print(f"founded users photos in albums:\n")

    counter = 1
    backup_choice = {}
    ids = []

    for status, items in albums.items():
        if status == 'service':
            for item in items['items']:
                print(f"{counter}. {item['title']:.<24} {item['size']}")
                backup_choice[counter] = [{'id': item['id'], 'album_title': item['title']}]
                counter += 1

        elif status == 'user albums':
            for item in items['items']:
                if item['id'] not in [-6, -7, -15, -9000]:
                    ids.append({'id': item['id'], 'album_title': item['title']})
            print(f"{counter}. {status:.<24} {items['size']}")
            backup_choice[counter] = ids
            counter += 1
            ids = []

        else:
            for item in items['items']:
                ids.append({'id': item['id'], 'album_title': item['title']})
            print(f"{counter}. {status:.<24} {items['size']}")
            backup_choice[counter] = ids
            counter += 1
            ids = []

    back_up = (int(input(f"\nwhich albums to backup, choice [1-{counter - 1}]: ")))
    return backup_choice[back_up]