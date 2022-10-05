import json
import re

import httpx

from nonebot import on_command, on_keyword
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import ArgPlainText
from nonebot.params import CommandArg

KFC_eat = on_command("kfc", aliases={'肯德基'})
Crazy_cmd = on_command("crazy", aliases={'疯狂星期四'})
Crazy_txt = on_keyword(keywords={'疯狂星期四', 'v我50'})


class KFC:
    """肯德基类（迫真）"""

    def __init__(self):
        self.url_city = "https://selectstore.hwwt8.com/store-portal/wx/api/city/cities"
        self.url_store = "https://orders.kfc.com.cn/preorder-portal/wx/api/store/searchAllByCityCode"
        self.url_session = "https://orders.kfc.com.cn/preorder-portal/wx/api/init/initSession"
        self.url_menu = "https://orders.kfc.com.cn/preorder-portal/wx/api/menu/getMenuByStore"
        self.pic_host = 'https://pcp-pic.hwwt8.com'
        self.tencent_map = 'https://apis.map.qq.com/ws/geocoder/v1/'
        self.key = 'RPEBZ-J2ZWW-2CIRC-OO3Q2-HH7X2-7GBEJ'  # 腾讯地图api的后台key
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
                          '53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501',
            'Referer': 'https://servicewechat.com/wx23dde3ba32269caa/280/page-frame.html'
        }

    def get_location(self, keyword: str):
        """腾讯地图api 获取地区经纬度"""
        params = {
            'address': keyword,
            'key': self.key
        }
        resp = httpx.get(
            url=self.tencent_map,
            headers=self.headers,
            params=params
        )
        json_str = json.loads(resp.text)
        if json_str.get('result'):
            location = json_str['result']['location']
            lng = location['lng']
            lat = location['lat']
            return lng, lat
        else:
            return None, None

    async def get_city_id(self, param_city: str):
        """根据关键词查询城市或地区对应的id和经纬度"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url=self.url_city,
                headers=self.headers,
            )
            resp_json = json.loads(resp.text)
            city_list = resp_json['data']['allCities']
            for city in city_list:
                city_name = city['cityNameZh']
                district_name = city['districtName']
                if param_city in city_name and district_name == '':
                    return city['cityCode'], \
                           city['latitude'], \
                           city['longitude']
                if param_city in district_name:
                    lng, lat = self.get_location(param_city)
                    return city['cityCode'], lat, lng
            return None, None, None

    async def get_store_list(
            self,
            city_code: str,
            mylng: str,
            mylat: str
    ) -> tuple[str, list]:
        """根据城市id、经纬度查询店铺名字的列表以及对应id"""
        async with httpx.AsyncClient() as client:
            data = {
                'cityCode': city_code,
                'mylng': mylng,
                'mylat': mylat
            }
            resp = await client.post(
                url=self.url_store,
                headers=self.headers,
                data=data
            )
            resp_json = json.loads(resp.text)
            data_list = resp_json['data']['stores']
            store_list, i, store_id_list = '', 0, []
            for store_name in data_list:
                store_list += str(i) + '.' + \
                              store_name['storename'] + '\n'
                store_code = store_name['storecode']
                store_id_list.append(store_code)
                i += 1
            store_list += "----------------\n" \
                          "Tips：直接发送列表序号的数字即可"
            return store_list, store_id_list

    async def get_cookie(self):
        """获取临时会话的session"""
        resp = httpx.post(url=self.url_session)
        cookie = resp.cookies.get('koa.sid')
        return cookie

    async def get_menu(self, store_code: str):
        """根据店铺id获取菜单"""
        async with httpx.AsyncClient() as client:
            cookie = await self.get_cookie()
            data = {
                'storeCode': store_code
            }
            headers = {
                'User-Agent':
                    'Mozilla/5.0 (Windows NT 6.1; WOW64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
                    '53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501',
                'Cookie': 'koa.sid={}'.format(cookie)
            }
            resp = await client.post(
                url=self.url_menu,
                headers=headers,
                data=data
            )
            resp_json = json.loads(resp.text)
            menu_detail = resp_json['data']['data']
            menu_list, i = '', 0
            for food in menu_detail:
                food_name = food['nameCn'].replace('BBN', '')
                menu_list += str(i) + '.' + food_name + '\n'
                i += 1
            menu_list += "----------------\n" \
                         "Tips：直接发送列表序号的数字即可"
            return menu_list, menu_detail

    async def get_food(self, menu_detail: list, number: int):
        """拿到每种菜单主题下的食物"""

        def traversal(lists):
            food_result = ''
            for food in lists['menuList']:
                food_name = food['nameCn'].replace('BBN', '')
                food_name = '✨' + food_name + '✨' + '\n'
                if food['descCn']:
                    detail = food['descCn'] + '\n'
                else:
                    detail = ''
                if food['price'] != '0':
                    price = int(food['price']) / 100
                else:
                    price = int(food['priceHead']) / 100
                price_str = "【" + str(price) + "元起】\n"
                img_url = food['imageUrlNew']['M']
                img = MessageSegment.image(
                    self.pic_host + img_url
                )
                food_result += food_name
                food_result += detail + price_str + img
                food_result += '-----------------\n'
            return food_result

        menu = menu_detail[number]
        if menu.get('childClassList'):
            food_result_ = ''
            for lists_ in menu['childClassList']:
                food_result_ += traversal(lists_)
            return food_result_
        else:
            food_result_ = traversal(menu)
            return food_result_


@KFC_eat.handle()
async def kfc_eat(matcher: Matcher, args: Message = CommandArg()):
    plain_text = args.extract_plain_text()
    if plain_text:
        matcher.set_arg("city", args)  # 如果用户发送了参数则直接赋值


Store = []
Menu = []
Food = []


@KFC_eat.got("city", prompt="请输入您所在的城市或地区（县）")
async def city_handler(city: str = ArgPlainText("city")):
    global Store
    city_id, mylat, mylng = await KFC().get_city_id(city)
    if city_id:
        store_list, Store = await KFC().get_store_list(
            city_code=city_id,
            mylat=mylat,
            mylng=mylng
        )
        await KFC_eat.send(store_list)
    else:
        await KFC_eat.reject('没有相关地区信息，请重新输入！')


@KFC_eat.got("store")
async def store_handler(store: str = ArgPlainText("store")):
    global Store, Menu, Food
    if '退出' in store:
        await KFC_eat.finish('退出查询成功')
    if not re.match('[0-99]?', store):
        await KFC_eat.reject('您输入的序号有误，请重新输入')
    else:
        store_id = Store[int(store)]
        menu_list, Food = await KFC().get_menu(store_id)
        await KFC_eat.send(menu_list)


@KFC_eat.got("food")
async def food_handler(food: str = ArgPlainText("food")):
    global Food
    if '退出' in food:
        await KFC_eat.finish('退出查询成功')
    if not re.match('[0-99]?', food):
        await KFC_eat.reject('您输入的序号有误，请重新输入')
    else:
        food_results = await KFC().get_food(Food, int(food))
        await KFC_eat.finish(food_results)

# @Crazy_cmd.handle()
# async def
