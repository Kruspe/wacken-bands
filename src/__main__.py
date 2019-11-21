import json
import sys
import requests

# ARTISTS_URL = 'https://www.wacken.com/de/programm/bands/?type=1541083944&tx_woamanager_pi2%5Bfestival%5D=4&tx_woamanager_pi2%5Bperformance%5D=1%2C7&tx_woamanager_pi2%5Baction%5D=list&tx_woamanager_pi2%5Bcontroller%5D=AssetJson&cHash=4aaeb0a4c6c3f83fbdd4013abb42357d'

# def get_artists():
    # loads = json.loads(requests.get(ARTISTS_URL).content)
    # for artist in loads:
    #     print(artist['artist']['title'])
    #     artist['artist']['country'] = [c['isoCodeA2'] for c in artist['artist']['country']]
    #     print(artist)
    #     yield artist


# artists = None
# if __name__ == '__main__':
#     get_artists()

# def get_img_url(uid):
#     url = 'https://www.wacken.com/index.php?id=166&type=1541083933&L=0&tx_woamanager_pi2[controller]=Application&tx_woamanager_pi2[action]=getThumbnail&tx_woamanager_pi2[uid]={uid}&tx_woamanager_pi2[crop]=1&tx_woamanager_pi2[width]=440&tx_woamanager_pi2[height]=250'
#
#     html_doc = requests.get(url).content
#
#     soup = BeautifulSoup(html_doc, 'html.parser')
#
#     return 'https://www.wacken.com' + list(soup.find_all('img'))[0].get('src')
#
#
# artists = None
#
#
# def load_and_save_artists():
#     global artists
#     artists = get_artists()
#     with open('artists.json', mode='w') as f:
#         json.dump(list(artists), f)
#
#
# if sys.argv[1].lower() == 'artists':
#     load_and_save_artists()
# elif sys.argv[1].lower() == 'img':
#     if len(sys.argv) >= 3:
#         with open(sys.argv[2]) as f:
#             artists = json.load(f)
#     else:
#         load_and_save_artists()
#     imgs = {}
#     for artist in artists:
#         imgs[artist['artist']['uid']] = get_img_url(artist['artist']['uid'])
#     with open('imgs.json', mode='w') as f:
#         json.dump(imgs, f)
#
# uids = [a['uid'] for a in json.loads(artists)]
# print(uids)
# print(get_img_url(5))
