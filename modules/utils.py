def select_albums_to_backup(albums):
    """
    формирует меню для выбора альбомов для сохранения
    возвращает словарь с индетификаторами и названиями альбомов для сохранения
    """
    print(f"founded photos:\n")

    counter = 1
    data_for_backup = {}
    ids = []

    for status, items in albums.items():
        if status == 'service':
            for item in items['items']:
                print(f"{counter}. {item['title']:.<24} {item['size']}")
                data_for_backup[counter] = [{
                    'album_id': item['id'],
                    'album_title': item['title'],
                    'album_size': item['size'],
                }]
                counter += 1

        elif status == 'user albums':
            for item in items['items']:
                if item['id'] not in [-6, -7, -15, -9000]:
                    ids.append({
                        'album_id': item['id'],
                        'album_title': item['title'],
                        'album_size': item['size'],
                    })
            print(f"{counter}. {status:.<24} {items['size']}")
            data_for_backup[counter] = ids
            counter += 1
            ids = []

        else:
            for item in items['items']:
                ids.append({
                    'album_id': item['id'],
                    'album_title': item['title'],
                    'album_size': items['size'],
                })
            print(f"{counter}. {status:.<24} {items['size']}")
            data_for_backup[counter] = ids
            counter += 1
            ids = []

    select = (int(input(f"\nselect albums to backup [1-{counter - 1}]: ")))
    return data_for_backup[select]