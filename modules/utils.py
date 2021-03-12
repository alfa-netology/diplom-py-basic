from pprint import pprint

def select_albums_to_backup(albums):
    """
    формирует меню для выбора альбомов для сохранения
    возвращает словарь с индетификаторами, названиями и общим размером альбомов для сохранения
    """
    print(f"founded photos:\n")

    counter = 1
    data_for_backup = {}
    items = []

    for status, albums in albums.items():
        if status == 'service':
            for album in albums['items']:
                print(f"{counter}. {album['title']:.<24} {album['size']}")
                data_for_backup[counter] = [{
                    'album_id': album['id'],
                    'album_title': album['title'],
                    'album_size': album['size'],
                }]
                counter += 1

        elif status == 'user albums':
            for album in albums['items']:
                if album['id'] not in [-6, -7, -15, -9000]:
                    items.append({
                        'album_id': album['id'],
                        'album_title': album['title'],
                        'album_size': albums['total_size'],
                    })
            print(f"{counter}. {status:.<24} {albums['total_size']}")
            data_for_backup[counter] = items
            counter += 1
            items = []

        else:
            for album in albums['items']:
                items.append({
                    'album_id': album['id'],
                    'album_title': album['title'],
                    'album_size': albums['total_size'],
                })
            print(f"{counter}. {status:.<24} {albums['total_size']}")
            data_for_backup[counter] = items
            counter += 1
            items = []

    select = (int(input(f"\nselect albums to backup [1-{counter - 1}]: ")))
    return data_for_backup[select]
