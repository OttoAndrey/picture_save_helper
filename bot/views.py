import json
import os.path
from urllib.parse import urlparse

import requests
import vk_api
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from picture_save_helper.settings import VK_CONFIRMATION_CODE, VK_BOT_TOKEN, VK_SECRET_KEY
from vk_api.utils import get_random_id


def download_photo(photo):
    sizes = photo['sizes']
    last_size = sizes[-1]
    photo_url = last_size['url']
    photo_name = urlparse(photo_url).path.split('/')[-1]

    img_response = requests.get(photo_url)
    img_response.raise_for_status()

    with open(photo_name, 'wb') as file:
        file.write(img_response.content)

    return photo_name


def upload_image(vk_token, vk_upload_url, img):
    params = {'v': 5.126, 'access_token': vk_token}

    with open(img, 'rb') as file:
        url = vk_upload_url
        files = {'photo': file}
        upload_response = requests.post(url, files=files, params=params)
        upload_response.raise_for_status()
        upload_data = upload_response.json()

    return upload_data


@csrf_exempt
def picture_save_help(request):
    if not request.method == 'POST':
        return HttpResponse('ok', content_type='text/plain', status=200)

    data = json.loads(request.body)

    if not data['secret'] == VK_SECRET_KEY:
        return HttpResponse('ok', content_type='text/plain', status=200)

    if data['type'] == 'confirmation':
        return HttpResponse(VK_CONFIRMATION_CODE, content_type='text/plain', status=200)

    if data['type'] == 'message_new':
        vk_session = vk_api.VkApi(token=VK_BOT_TOKEN)
        vk = vk_session.get_api()

        from_id = data['object']['message']['from_id']
        attachments = data['object']['message']['attachments']

        try:
            photo = attachments[0]['photo']
        except IndexError:
            vk.messages.send(
                random_id=get_random_id(),
                peer_id=from_id,
                message=f'¯\_(ツ)_/¯',
            )
            vk.messages.delete_conversation(user_id=from_id,)
            return HttpResponse('ok', content_type='text/plain', status=200)
        except KeyError:
            vk.messages.send(
                random_id=get_random_id(),
                peer_id=from_id,
                message=f'¯\_(ツ)_/¯',
            )
            vk.messages.delete_conversation(user_id=from_id,)
            return HttpResponse('ok', content_type='text/plain', status=200)

        photo_name = download_photo(photo)
        vk_upload_url = vk.photos.get_messages_upload_server(
            access_token=VK_BOT_TOKEN,
            peer_id=0,
        )
        upload_data = upload_image(VK_BOT_TOKEN, vk_upload_url['upload_url'], photo_name)
        save_data = vk.photos.save_messages_photo(
            access_token=VK_BOT_TOKEN,
            server=upload_data['server'],
            photo=upload_data['photo'],
            hash=upload_data['hash'],
        )
        save_data = save_data[0]
        vk.messages.send(
            random_id=get_random_id(),
            peer_id=from_id,
            attachment=f'photo{save_data["owner_id"]}_{save_data["id"]}',
        )
        vk.messages.delete_conversation(user_id=from_id,)
        os.remove(photo_name)

        return HttpResponse('ok', content_type='text/plain', status=200)
