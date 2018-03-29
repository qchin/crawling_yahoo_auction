#!/usr/bin/python3
# coding: utf-8

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import re
import logging

logger = logging.getLogger('hello yahoo')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('yahoo_auction.log')
fh.setLevel(logging.INFO)
logger.addHandler(fh)

CHROME_DRIVER_EXE = 'X:\\selenium\\driver\\chromedriver.exe'
YAHOO_AUCTION_SEARCH_KEYWORD = '1円スタート'

def get_element_by_css_selector(driver, css_selector):
    el = None
    try:
        el = driver.find_element_by_css_selector(css_selector)
    finally:
        return el

def get_elements_by_xpath(driver, xpath):
    el = None
    try:
        el = driver.find_elements_by_xpath(xpath)
    finally:
        return el

def get_element_by_xpath(driver, xpath):
    el = None
    try:
        el = driver.find_element_by_xpath(xpath)
    finally:
        return el

def yha_get_search_page_current_id(driver):
    current_page = None
    nav_bar = get_element_by_css_selector(driver, 'p.mid')
    if nav_bar:
        all_children_by_xpath = get_elements_by_xpath(nav_bar, ".//*")
        if all_children_by_xpath:
            for child in all_children_by_xpath:
                if(child.tag_name == 'span'):
                     current_page = child.text
                     break
    return current_page

def yha_nav_search_page_with_num(driver, page_num):
    clicked = None
    nav_bar = get_element_by_css_selector(driver, 'p.mid')
    if nav_bar:
        all_children_by_xpath = get_elements_by_xpath(nav_bar, ".//*")
        if all_children_by_xpath:
            for child in all_children_by_xpath:
                if(child.text == str(page_num)):
                     child.click()
                     clicked = page_num + 1
                     break
    else:
        clicked = 1
    return clicked

def yha_search_page_get_user_name(driver):
    user_lists = {}
    try:
        els = driver.find_elements_by_css_selector('div.sinfwrp')
        for el in els:
            als = el.find_elements_by_xpath('.//div//p//a')
            for href in als:
                target = href.text
                if (target.find('評価') == -1 and target.find('非表示') == -1):
                    user_lists[target] = target
    finally:
        pass
    return user_lists

def yha_get_user_review_info(driver, xpath):
    user_total_review_list = {}
    total_review = driver.find_elements_by_xpath(xpath)
        
    for review in total_review:
       if (review.text.find('非常に良い・良い：') != -1 and
        review.text.find('どちらでもない：') != -1 and
        review.text.find('非常に悪い・悪い：') != -1):
            regex_text = '（([0-9]+)件）'
            pattern = re.compile(regex_text)
            review_list = pattern.findall(review.text)
            if (review_list != None and len(review_list) == 3):
                user_total_review_list['positive'] = review_list[0]
                user_total_review_list['neutral'] = review_list[1]
                user_total_review_list['negative'] = review_list[2]
            break
    return user_total_review_list

def yha_get_user_seller_negative_reviews(driver):
    user_negative_case_list = []
    line_list = driver.find_elements_by_xpath('//body//div//p//table//tbody//tr//td//table')
    for line in line_list:
        auction_item = {}
        if (line.get_attribute('innerHTML').find('RATING INFO') != -1):
            auction_name = get_element_by_xpath(line, './/tbody//tr//td//small//a')
            if auction_name:
                auction_item['商品名'] = auction_name.text
            comments = get_elements_by_xpath(line, './/tbody//tr//td//table//tbody//tr//td//small')
            last_label = 'コメント'
            for comment in comments:
                if (comment.text != 'すべてのコメント・返答を見る' and
                comment.text != 'コメント' and
                comment.text != '返答' and
                comment.text != '評価者'):
                    if last_label not in auction_item.keys():
                        auction_item[last_label] = comment.text
                else:
                    if (comment.text == 'コメント' or
                    comment.text == '返答' or
                    comment.text == '評価者'):
                        last_label = comment.text
        if len(auction_item) > 0:
            user_negative_case_list.append(auction_item)
    return user_negative_case_list

def show_recommend_user_info(total_info):
    for user_info in total_info:
        positive = total_info[user_info]['total_review']['positive']
        neutral = total_info[user_info]['total_review']['neutral']
        negative = total_info[user_info]['total_review']['negative']
        if (int(positive) > 100 and int(negative) == 0):
            print('おすすめ出品者 : ' + user_info + '\n' + 
            '非常に良い・良い : ' + positive + '\n' + 
            'どちらでもない : ' + neutral + '\n' + 
            '非常に悪い・悪い : ' + negative + '\n\n')

def main(_):
    driver = webdriver.Chrome(CHROME_DRIVER_EXE)
    driver.get('https://auctions.yahoo.co.jp/search/search?p=' + YAHOO_AUCTION_SEARCH_KEYWORD)

    next_page = 1
    user_list = {}
    while (True):
        tmp_list = yha_search_page_get_user_name(driver)
        for k,v in tmp_list.items():
            user_list[k] = v
        result = yha_nav_search_page_with_num(driver, next_page)
        if (result == None or result == 1):
            break
        next_page = next_page + 1
    
    user_info_list = {}
    for user in user_list.keys():
        # user's total review information
        driver.get('https://auctions.yahoo.co.jp/jp/show/rating?userID=' + user)
        
        user_info = {}
        user_total_review_list = {}
        user_negative_case_list = []
        user_total_review_list = yha_get_user_review_info(driver, '//body//div//table//tbody//tr//td//table//tbody//tr//td//table//tbody//tr//td//p//table//tbody//tr//td//table//tbody//tr//td//small')
        if (len(user_total_review_list) == 0):
            user_total_review_list = yha_get_user_review_info(driver, '//body//div//p//table//tbody//tr//td//table//tbody//tr//td//small')
        user_info['total_review'] = user_total_review_list 
        
        # negative reviews as seller
        driver.get('https://auctions.yahoo.co.jp/jp/show/rating?userID=' + user + '&role=seller&filter=-1')
        
        user_negative_case_list = yha_get_user_seller_negative_reviews(driver)
        user_info['seller_negative_case'] = user_negative_case_list 
        user_info_list[user] = user_info
        
    show_recommend_user_info(user_info_list)
    logger.info(user_info_list)

    driver.close()
    driver.quit()

if __name__ == "__main__":
    main(1)

"""
{
    "user1": {
        'total_review' : {
            'positive' : 8000,
            'neutral' : 5,
            'negative' : 30
        },
        'seller_negative_case' : [
            {
                '商品名' : '',
                'コメント' : '',
                '返答' : ''
            },
            {
                '商品名' : '',
                'コメント' : ''
            },
            {
                '商品名' : '',
                'コメント' : '',
                '返答' : ''
            }
        ]
    },
    'user2': {
...
}
"""
