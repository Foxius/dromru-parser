import asyncio
import aiohttp
import multiprocessing as mp
from bs4 import BeautifulSoup as bs
from threading import Thread, Lock
from multiprocessing import Manager
from time import time, sleep
import re as regex
from loguru import logger
import requests
import json
from queue import Queue
from DB import DataDb, SessionDb as sess
import csv
import traceback
min_price = 3500
max_price = 40000
proxy_key = '82f2bae68f1a03ffba8d809d1abdb396'
proxy_change = f"https://mobileproxy.space/reload.html?proxy_key={proxy_key}&format=json"
proxy = 'http://mproxy.site:11823'
proxy_auth = aiohttp.BasicAuth('UmGEX1', 'EBeRANduq6am')
q_number = asyncio.Queue()
q_number_2 = asyncio.Queue()
lock_a = asyncio.Lock()
lock = Lock()
last_change_ip = 0
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 OPR/94.0.0.0 (Edition Yx GX)'}
total_timeout =aiohttp.ClientTimeout(total=5)
async def pars1(loop):
    while True:
        num = await q_number.get()
        logger.info(f'pars1 -- {num}')
        url = f"https://baza.drom.ru/oem/{num}/?price_max={max_price}&price_min={min_price}#tab=cena"
        while True:
            try:
                async with aiohttp.ClientSession(loop=loop,timeout=total_timeout) as session:
                    async with session.request(url=url, method='GET', proxy=proxy, proxy_auth=proxy_auth, timeout=5) as resp:
                        Thread(target=check_1, args=[num, await resp.text()]).start()
                        break
            except:
                logger.debug(traceback.format_exc())
                pass


async def pars2(loop):
    while True:
        _num, _url, _p = await q_number_2.get()
        logger.info(f'pars2 -- {_num} -- {_url}')
        while True:
            try:
                async with aiohttp.ClientSession(loop=loop,timeout=total_timeout) as session:
                    async with session.request(url=_url, method='GET', proxy=proxy, proxy_auth=proxy_auth, timeout=5) as resp:
                        Thread(target=check_2, args=[_num, await resp.text(), _url, _p]).start()
                        break
            except:
                logger.debug(traceback.format_exc())
                pass


def change_ip():
    logger.info(f"Меняю IP")
    try:
        _resp = requests.get(proxy_change).text
        data = json.loads(_resp)
    except:
        logger.debug(traceback.format_exc())
        change_ip()
    if data['status'] == 'OK':
        logger.success(
            f"Cмена IP-адреса прошла успешно! Новый IP - {data['new_ip']}")
    if data['status'] == 'ERR':
        logger.error(f"Произошла ошибка при смене IP-адреса. Повторная смена")
        change_ip()


def check_1(number, page):
    global last_change_ip
    logger.info(f'check_1 -get -- {number}')
    page_soup = bs(page, 'html.parser')
    captcha = page_soup.find('h2', text='Вы не робот?')
    notif = page_soup.find(
        'div', text=' Мы искали для вас предложения со словом ')
    if captcha:
        lock.acquire()
        now = int(round(time(), 0))
        if now - last_change_ip > 20:
            last_change_ip = now
            lock.release()
            change_ip()
        try:
            lock.release()
        except:
            pass
        logger.info(f'check_1 -- {number} -- ref')
        q_number._queue.insert(0, number)
    else:
        page_cont = page_soup.find_all('span', class_='pagestat')
        if page_cont in (None, "", []):
            if notif:
                return ''
            else:
                page = 1
        else:
            text = page_cont[0].text
            page_count = regex.sub(r"[^\d]", "", text)
            page = int(round(int(page_count) / 50))
            for p in range(0, page):
                url = f"https://baza.drom.ru/oem/{number}/?price_max={max_price}&price_min={min_price}&page={p}#tab=cena"
                q_number_2.put_nowait([number, url, p])
                logger.info(f'check_1 -- {number} -- q2 -- put2')


def check_2(number: str, page: str, url: str, p):
    global last_change_ip
    logger.info(f'check_2 -get -- {number} -- {url}')
    links_soup = bs(page, 'html.parser')
    captcha = links_soup.find('h2', text='Вы не робот?')
    if captcha:
        lock.acquire()
        now = int(round(time(), 0))
        if now - last_change_ip > 20:
            last_change_ip = now
            lock.release()
            change_ip()
        try:
            lock.release()
        except:
            pass
        q_number_2._queue.insert(0, [number, url, p])
        logger.info(f'check_2 -- {number} -- ref')
    else:
        cards_link = links_soup.find_all(
            'a', class_='bulletinLink bull-item__self-link auto-shy')
        raw_price = links_soup.find_all(
            'span', class_="price-per-quantity__price")
        raw_manufacturer = links_soup.find_all(
            'div', class_="bull-item__annotation-row manufacturer")
        fd = zip(raw_manufacturer, raw_price, cards_link)
        lst_adds = []
        for i in fd:
            link = f"https://baza.drom.ru{i[2].get('href')}"
            data = DataDb(manufacruter=i[0].text,
                          number=number, price=i[1].text, link=link)
            lst_adds.append(data)
            logger.success(
                f"Запись - {i[0].text} - {number} -- page({p}) - {i[1].text} - {link}")
        lock.acquire()
        sess.rollback()
        sess.add_all(lst_adds)
        sess.commit()
        sleep(2)
        lock.release()


async def main(loop):
    await asyncio.gather(pars1(loop), pars2(loop),pars1(loop), pars2(loop),pars1(loop), pars2(loop), pars2(loop), pars2(loop),)


if __name__ == '__main__':

    all_ = sess.query(DataDb.number).all()
    all_ = set([i[0] for i in all_])
    reader = csv.reader(open("numbersdatabase.csv"))
    reader = list(reader)
    reader = set([i[0] for i in reader])
    rows = 0
    for row in reader - all_:
        rows += 1
        q_number.put_nowait(row)
    print(f'Start... {rows}')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
