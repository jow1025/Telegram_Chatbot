import telegram
import requests
from telegram.ext import Updater
from telegram.ext import MessageHandler, Filters
from bs4 import BeautifulSoup 
from selenium import webdriver
import urllib.request as req
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
API_key='공공데이터 버스도착정보 API 키'

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument("disable-gpu")
# 혹은 options.add_argument("--disable-gpu")
driver  = webdriver.Chrome("./chromedriver.exe", options = options) 
#확진자 검색 후 f12로 코로나 확진자 수 정보 컴포넌트 위치 파악 후 크롤링
def covid_num_crawling():
    code = req.urlopen("https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=%ED%99%95%EC%A7%84%EC%9E%90")
    soup = BeautifulSoup(code, "html.parser")
    info_num = soup.select("div.status_info em")
    result = info_num[0].string 
    return result
 
def covid_news_crawling():
    code = req.urlopen("https://search.naver.com/search.naver?where=news&sm=tab_jum&query=%EC%BD%94%EB%A1%9C%EB%82%98")
    soup = BeautifulSoup(code, "html.parser")
    title_list = soup.select("a.news_tit")
    output_result = ""
    for i in title_list:
        title = i.text
        news_url = i.attrs["href"]
        output_result += title + "\n" + news_url + "\n\n"
        if title_list.index(i) == 2:
            break
    return output_result
 
def covid_image_crawling(image_num=5):
    if not os.path.exists("./코로나이미지"):
        os.mkdir("./코로나이미지")
 
    browser = webdriver.Chrome("./chromedriver")
    browser.implicitly_wait(3)
    wait = WebDriverWait(browser, 10)
 
    browser.get("https://search.naver.com/search.naver?where=image&section=image&query=%EC%BD%94%EB%A1%9C%EB%82%98&res_fr=0&res_to=0&sm=tab_opt&color=&ccl=0&nso=so%3Ar%2Cp%3A1d%2Ca%3Aall&datetype=1&startdate=&enddate=&gif=0&optStr=d&nq=&dq=&rq=&tq=")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.photo_group._listGrid div.thumb img")))
    img = browser.find_elements_by_css_selector("div.photo_group._listGrid div.thumb img")
    for i in img:
        img_url = i.get_attribute("src")
        req.urlretrieve(img_url, "./코로나이미지/{}.png".format(img.index(i)))
        if img.index(i) == image_num-1:
            break
    browser.close()

def melon_chart_crawling():
    addr = 'https://www.melon.com/chart/index.htm'

    driver.get(addr)
    melon = driver.page_source
    soup = BeautifulSoup(melon, 'html.parser')
    title = soup.select('#frm > div div.ellipsis.rank01 > span > a')
    artist = soup.select('#frm > div div.ellipsis.rank02 > span > a')

    titles = []
    for i,j in enumerate(title):
        if i < 10:
            tts = str(i) + ' ' + j.get_text()
            titles.append(tts)

    artists = []
    for i, j in enumerate(artist):
        if i < 10:
            tts = j.get_text()
            artists.append(tts)

    key_val = [titles, artists]
    # rank_text = dict(zip(*key_val))
    
    #titles, artists 는 .text필드 없음, str로 파싱 후 title은 앞자리2번째부터
    output=" "
    #10개. 더 구하고싶으면 더 조절
    for i in range (0,10):
        output+=str(i+1)+'위: '+str(titles[i][2:])+"-"+str(artists[i])+'\n'
            
    return output

def movie_chart_crawling():
    session=requests.Session()
    #영화 크롤링 사이트
    addr='http://movie.naver.com/movie/running/current.nhn'
    req=session.get(addr)
    soup=BeautifulSoup(req.text,'html.parser')
    titles=soup.find_all('dl',class_='lst_dsc')
    cnt=1
    output=" "

    # 영화제목+ 링크가 순서대로 5개 출력되고 각 영화별 설명이 짤막하게 들어가고 + 출력까지 
    for title in titles:
        output+=str(cnt)+'위: '+title.find('a').text+'\n'+addr+title.find('a')['href']+'\n'
        #여기서 푸쉬해서 5개 각 저옵가 메세지로 출력되게끔
        bot.send_message(chat_id=id,text=output)
        output="" 
        cnt+=1
        if cnt==6:
            break
    #return output 
  
def bus_crawling(message):
    serviceKey=API_key

    #버스 Id와, 버스이름 매칭
    #노선id==버스id라고 생각하자.
    route_7_list={
        '100100316':'6642',
        '100100307':'6630',
        '100100309':'6632',
        '232000067':'388김포',
        #위 4개: 7단지정류소
        }

    #route_4_list={'115900005':'강서05'}
    out_put1=[]
    if message=="버스":
        for routeId,bus_num in route_7_list.items():
            #7단지 정류소 id
            stationId="115000302"
            #버스 ID
            routeId=str(routeId)
            url="http://ws.bus.go.kr/api/rest/arrive/getArrInfoByRouteAll?serviceKey={}&stId={}&busRouteId={}".format(serviceKey,stationId,routeId)
            response=requests.get(url).text
            soup = BeautifulSoup(response, "html.parser")
            print(soup.arrmsg1)
            out_put1.append([bus_num,soup.arrmsg1.text,soup.arrmsg2.text])
        msg=''
        for val in out_put1:
            msg+='{}\n 첫번째: {}\n 두번째: {}\n'.format(val[0],val[1],val[2])       
        return msg

def n_weather_crawling():
    url="https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=%EB%B0%9C%EC%82%B01%EB%8F%99%EB%82%A0%EC%94%A8"
    r=requests.get(url)
    soup=BeautifulSoup(r.text,'html.parser')
    weather_info=soup.select("div.today_area>div.main_info")
    if len(weather_info) >0:
        temperature=soup.select("span.todaytemp")
        cast_text=soup.select("p.cast_txt")
        indicator=soup.select("span.indicator")
        if len(temperature) >0 and len(cast_text)>0 and len(indicator)>0:
            temperature=temperature[0].text.strip()
            indicator=indicator[0].text.strip()
            txt=cast_text[0].text.strip()
            weather="{}도\r\n{}\r\n{}".format(temperature,indicator,txt)
        return weather



#토큰 넘버
token = "토큰"
id = "id값"
 
bot = telegram.Bot(token)
info_message = '''- 오늘 확진자 수 확인 : "코로나" 입력
- 코로나 관련 뉴스 : "뉴스" 입력
- 실시간 멜론차트10순위: "멜론" 입력
- 코로나 관련 이미지 : "이미지" 입력
- 네이버 영화 순위: "영화" 입력
- 버스 도착 정보:  "버스" 입력
- 동네 날씨 정보: :동네날씨" 입력 '''
bot.sendMessage(chat_id=id, text=info_message)
 
updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher
updater.start_polling()
 
### 챗봇 답장
def handler(update, context):
    user_text = update.message.text # 사용자가 보낸 메세지를 user_text 변수에 저장
    # 오늘 확진자 수 답장
    if (user_text == "코로나"):
        covid_num = covid_num_crawling()
        bot.send_message(chat_id=id, text="오늘 확진자 수 : {} 명".format(covid_num))
        bot.sendMessage(chat_id=id, text=info_message)
    # 코로나 관련 뉴스 답장
    elif (user_text == "뉴스"):
        covid_news = covid_news_crawling()
        bot.send_message(chat_id=id, text=covid_news)
        bot.sendMessage(chat_id=id, text=info_message)
    # 코로나 관련 이미지 답장
    elif (user_text == "이미지"):
        bot.send_message(chat_id=id, text="최신 이미지 크롤링 중...")
        covid_image_crawling(image_num=10)
        # 이미지 한장만 보내기
        # bot.send_photo(chat_id=id, photo=open("./코로나이미지/0.png", 'rb'))
        # 이미지 여러장 묶어서 보내기
        photo_list = []
        for i in range(len(os.walk("./코로나이미지").__next__()[2])): # 이미지 파일 개수만큼 for문 돌리기
            photo_list.append(telegram.InputMediaPhoto(open("./코로나이미지/{}.png".format(i), "rb")))
        bot.sendMediaGroup(chat_id=id, media=photo_list)
        bot.sendMessage(chat_id=id, text=info_message)
    elif( user_text=="멜론"):
        bot.send_message(chat_id=id, text="조회 중 입니다...")
        melon_chart=melon_chart_crawling()
        bot.send_message(chat_id=id, text=melon_chart)
        bot.sendMessage(chat_id=id, text=info_message)
    elif(user_text=="영화"):
        bot.send_message(chat_id=id, text="조회 중 입니다...")
        movie_chart=movie_chart_crawling()
        #출력은 위의 함수 내부에서 한다.
        #bot.send_message(chat_id=id,text=movie_chart)
        bot.sendMessage(chat_id=id,text=info_message)
        #마을버스: 단일 '5번버스'만 통행함
        #7단지: 여러 버스가 통행함
    elif(user_text=="버스"):
        bus_info=bus_crawling(user_text)
        bot.send_message(chat_id=id,text=bus_info)
        bot.sendMessage(chat_id=id,text=info_message)
    elif(user_text=="동네날씨"):
        #n: neighbor
        n_weather=n_weather_crawling()
        bot.send_message(chat_id=id,text=n_weather)
        bot.sendMessage(chat_id=id,text=info_message)    
    
        
echo_handler = MessageHandler(Filters.text, handler)
dispatcher.add_handler(echo_handler)