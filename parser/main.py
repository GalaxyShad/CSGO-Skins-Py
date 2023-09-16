from typing import Any
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import time
import requests
import re
import os
import random
import enum

from dataclasses import dataclass

from requests import Response
from bs4 import BeautifulSoup as bs, NavigableString, ResultSet, Tag

import json

REQ_DELAY = 300
REQ_PAUSE = 5

CSGO_STASH_URL = 'https://csgostash.com'

DELAY_429_SEC = 300


def get_page(url: str) -> bs :
    tries_429 = 0

    while True:
        try:
            req: Response = requests.get(url)
        except ConnectionError as err:
            print(f'[Connection Error] Check connection, Retrying... {err}')
            continue
        except TimeoutError as err:
            print(f'[Timeout Error] Retrying... {err}')
            continue
        except err:
            print(f'[Unhandled Error] Retrying... {err}')
            raise

        match req.status_code:
            case 200:
                page = bs(req.text, "html.parser")
                return page
            case 429:
                print(f'[Too Many Requests 429] try: #{tries_429}')
                if tries_429 == 0:
                    tries_429 += 1
                    continue
                elif tries_429 < 3:
                    print('Waiting 3 secs')
                    time.sleep(3)
                    continue
                else:
                    print(f'Waiting {DELAY_429_SEC} secs')
                    time.sleep(DELAY_429_SEC) 
            case _:
                print(f'[Unhandled HTTP Error] {req.status_code}')
                req.raise_for_status()
    pass



def get_result_boxes_from_page(page_url: str) -> ResultSet[Any] :
    bs_page = get_page(CSGO_STASH_URL + page_url)
    result_box_list = bs_page.find_all('div', class_='result-box')
    bs_page.find()
    return result_box_list

@dataclass
class ResultBox:
    title: str
    link: str | None
    img_url: str

def parse_result_box(result_box: Tag | NavigableString) -> ResultBox:
    h = result_box.find('h3') or result_box.find('h4')
    
    title = h.extract().get_text() 
    img_url = result_box.find('img').get('src')

    a_href: Tag = result_box.find('a', class_=None)
    link = (a_href or None) and a_href.get('href')

    return ResultBox(title, link, img_url)


def parse_result_box_list(result_box_list: ResultSet[Tag]):
    parsed_list = []
    
    for result_box in result_box_list:
        if result_box.find('script') is not None:
            continue

        parsed_list.append(parse_result_box(result_box))

    return parsed_list

class WeaponQualityType(enum.Enum):
    CONSUMER_GRADE = 0
    INDUSTRIAL_GRADE = 1
    MIL_SPEC = 2
    RESTRICTED = 3
    CLASSIFIED = 4
    COVERT = 5
    KNIVES = 6
    GLOVES = 7
    CONTRABAND = 8
    UNKNOWN = 9

@dataclass
class WeaponPriceList:
    factory_new: str | None
    minimal_wear: str | None
    field_tested: str | None
    well_worn: str | None
    battle_scarred: str | None


@dataclass
class Weapon:
    name: str
    is_stattrack_available: bool
    quality: WeaponQualityType
    price_list: WeaponPriceList
    price_list_stattrak: WeaponPriceList | None
    img_url: str


# def concat_heading(heading: Tag) -> str:
#     str_heading = ''
    
#     str.join()

#     map(lambda x:Tag : x., heading.findChildren())

#     for tag in heading.findChildren():
#         str_heading

def parse_price_list(tabpanel: ResultSet[Tag]) -> tuple[WeaponPriceList]:
    price_dict = {}
    price_stattrak_dict = {}

    for div in tabpanel:
        if 'price-bottom-space' in div.attrs['class'] or \
           'price-modified-time' in div.attrs['class']:
            continue

        spans = div.find_all('span')
        span_price_text: str = spans[-1].get_text()
        span_qulity_text: str = spans[-2].get_text()
        span_additional_text: str = spans[-3].get_text() if len(spans) >= 3 else None

        price = span_price_text if span_price_text != 'Not Possible' else None

        match span_additional_text:
            case 'Souvenir': pass 
            case 'StatTrak': price_stattrak_dict[span_qulity_text] = price
            case _: price_dict[span_qulity_text] = price

    return WeaponPriceList(
        factory_new=price_dict.get('Factory New'),
        minimal_wear=price_dict.get('Minimal Wear'),
        field_tested=price_dict.get('Field-Tested'),
        well_worn=price_dict.get('Well-Worn'),
        battle_scarred=price_dict.get('Battle-Scarred')
    ), WeaponPriceList(
        factory_new=price_stattrak_dict.get('Factory New'),
        minimal_wear=price_stattrak_dict.get('Minimal Wear'),
        field_tested=price_stattrak_dict.get('Field-Tested'),
        well_worn=price_stattrak_dict.get('Well-Worn'),
        battle_scarred=price_stattrak_dict.get('Battle-Scarred')
    ), 

def color_to_quality(color: str) -> WeaponQualityType:
    match color:
        case 'color-consumer': return WeaponQualityType.CONSUMER_GRADE
        case 'color-industrial': return WeaponQualityType.INDUSTRIAL_GRADE
        case 'color-milspec': return WeaponQualityType.MIL_SPEC
        case 'color-restricted': return WeaponQualityType.RESTRICTED
        case 'color-classified': return WeaponQualityType.CLASSIFIED
        case 'color-covert': return WeaponQualityType.COVERT
        case 'color-contraband': return WeaponQualityType.CONTRABAND
        case _: return WeaponQualityType.UNKNOWN


def parse_weapon_from_url(url: str) -> Weapon:
    bs_page = get_page(url)

    name: str = bs_page.find('h2').get_text()
    img_url: str = bs_page.find('img', class_='main-skin-img').get('src')
    is_stattrack_available: bool = True if bs_page.find('div', class_='stattrak') else False
    
    quality_color =  bs_page.find('div', class_='quality').get_attribute_list('class')[-1]
    quality = color_to_quality(quality_color)

    tabpanel = bs_page.find('div', id='prices').find_all('div')
    price_list, price_list_stattrak = parse_price_list(tabpanel)

    return Weapon(name=name, 
                  img_url=img_url,
                  quality=quality, 
                  is_stattrack_available=is_stattrack_available,
                  price_list=price_list,
                  price_list_stattrak=price_list_stattrak if is_stattrack_available else None
                  )


def get_case_list():
    case_dict = {}

    bs_page = get_page(CSGO_STASH_URL)

    li_list = bs_page.find('li', string='Newest Cases').parent.find_all('li')
    for li in li_list:
        if len(li.attrs) != 0 and \
            ('divider' in li.attrs['class'] or \
            'dropdown-header' in li.attrs['class']):
            continue

        a: Tag = li.find('a')
        name = a.get_text()

        case_dict[name] = a.get('href')

    return case_dict


def main():
    # result_boxes = get_result_boxes_from_page('/weapon/AK-47')
    # parsed = parse_result_box_list(result_boxes)
    # parsed = parse_weapon_from_url('https://csgostash.com/skin/1550/M4A4-Temukau')
    
    result_boxes = get_result_boxes_from_page('/containers/skin-cases')
    parsed = parse_result_box_list(result_boxes)

    # get_case_list()

    pass


if __name__ == '__main__':
    main()

