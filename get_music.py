import re
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}


def get_music(name, page=1):
    url = 'https://deqing.ricuo.com/'
    payload = {
        'input': name,
        'filter': "name",
        'type': 'netease',
        'page': page,
    }
    try:
        response = requests.post(url, data=payload, headers=headers)
        code = response.json().get('code', 403)
        song_infos =[]
        if code == 200:
            data = response.json().get('data', [])
            for item in data:
                lrc = item.get('lrc', "")
                author = item.get('author', "")
                play_url = item.get('url', "")
                title = item.get('title', "")
                pic = item.get('pic', "")
                wording_list = re.findall(r'作词 :(.*?)\n', lrc)
                musicing_list = re.findall(r'作曲 :(.*?)\n', lrc)
                wording = wording_list[0] if wording_list else ""
                musicing = musicing_list[0] if musicing_list else ""
                song_infos.append([title, author, pic, wording, musicing, play_url])
        else:
            return False, song_infos
    except:
        return False, song_infos
    return True, song_infos


if __name__ == '__main__':
    name = '成都'
    page = 1
    ret, song_infos = get_music(name, page)
    print(song_infos)