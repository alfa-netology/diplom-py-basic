import modules.colors as colors

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
                data_for_backup[counter] = [{
                    'album_id': album['id'],
                    'album_title': album['title'],
                    'album_size': album['size'],
                }]
                print(f"{counter}. {album['title']:.<24} {album['size']}")
                counter += 1
        else:
            for album in albums['items']:
                items.append({
                    'album_id': album['id'],
                    'album_title': album['title'],
                    'album_size': albums['total_size'],
                })
            data_for_backup[counter] = items
            print(f"{counter}. {status:.<24} {albums['total_size']}")
            counter += 1
            items = []

    while True:
        select = (int(input(f"\nselect albums to backup [1-{counter - 1}]: ")))
        if select not in range(1, counter):
            print(counter)
            print(f"\n{colors.FAILURE} {select} not in range [1-{counter - 1}], let's try again.")
        else:
            break

    return data_for_backup[select]
