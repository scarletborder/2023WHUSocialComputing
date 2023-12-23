from DrissionPage import ChromiumPage

# 粉丝用户`属性，list[list]
UserListDate = list()
UserListIP = list()
UserListFilmNum = list()
# 影片评分
m2score = list()


class NoneEle:
    text = ""


class Config:
    ReviewCnt: int = 100


Cfg = Config()


def getLongReview(url: str):
    """
    # 获取长评的数据
    ## params
    - url: string，电影的门户页面
    - rate: 你想获得的评分，[1,5(included)]
    - return:`None | tuple[str, str, str, int]`
        - 返回值为空则结束
        - 第一个返回值是评论字符串，
        - 之后三个分别为ip属地，创号时间，看过电影的数量。
        - 如果没有用户信息如销号则后三个参数都返回"", "", -1
        - 缺失的数据用"",-1替代
    """
    baseUrl = url + r"reviews?sort=time" + "&start="
    pagecnt = 0
    page = ChromiumPage()
    cnt = 0  # 记录获得的评论数量
    while cnt < Cfg.ReviewCnt:
        page.get(baseUrl + str(pagecnt))
        try:
            review_list = page.ele(r"css:div[class='review-list  ']", timeout=5)
        except BaseException:
            return "", "", "", -1
        review_list = review_list.eles(r"css:div[data-cid]")
        if len(review_list) == 0:
            return "", "", "", -1
        for item in review_list:
            item.ele(r'css:a[class="unfold"][title="展开"]').click()
            userUrl = item.ele(r'css:a[class="avator"]').attr("href")
            newtab = page.new_tab(str(userUrl))

            # 用户属性
            date: str = ""
            location = ""
            filmNum = -1

            try:
                userInfo = newtab.ele(".user-info", timeout=5).ele(
                    'css:div[class="pl"]'
                )
            except BaseException:
                pass
            else:
                userInfo = userInfo.text.split("\n")
                for info in userInfo:
                    if info.find("加入") != -1:
                        date = info.strip("加入")
                    elif info.find("IP") != -1:
                        location = info.split("：")[-1]
            try:
                userMovie = newtab.ele("#movie", timeout=5).ele(".pl", timeout=5)
                userMovie = userMovie.text.split(" ")
            except BaseException:
                pass
            else:
                for info in userMovie:
                    if info.find("看过") != -1:
                        filmNum = info.strip("部看过")
                        break

            # 详细评论
            newtab.close()
            page.wait.load_complete()
            try:
                fullReview = item.ele(
                    r'css:div[class="review-content clearfix"]', timeout=5
                )
            except BaseException:
                fullReview = NoneEle()

            cnt += 1
            if cnt > Cfg.ReviewCnt:
                return fullReview.text, date, location, filmNum
            else:
                try:
                    yield fullReview.text, date, location, filmNum
                except BaseException:
                    yield "", "", "", -1

        pagecnt += 20


import jieba


def loadDict(fileName, score):
    wordDict = {}
    with open(fileName, "r", encoding="utf-8") as fin:
        for line in fin:
            word = line.strip()
            wordDict[word] = score
    return wordDict


def appendDict(wordDict, fileName, score):
    with open(fileName, "r", encoding="utf-8") as fin:
        for line in fin:
            word = line.strip()
            wordDict[word] = score


def loadExtentDict(dir):
    """
    记得dir文件夹名最后要加'/'
    """
    extentDict = {}
    with open(dir + "0.5" + "倍.txt", "r", encoding="utf-8") as fin:
        for line in fin:
            word = line.strip()
            extentDict[word] = 0.5
    with open(dir + "0.8" + "倍.txt", "r", encoding="utf-8") as fin:
        for line in fin:
            word = line.strip()
            extentDict[word] = 0.8
    with open(dir + "1.2" + "倍.txt", "r", encoding="utf-8") as fin:
        for line in fin:
            word = line.strip()
            extentDict[word] = 1.2

    with open(dir + "1.5" + "倍.txt", "r", encoding="utf-8") as fin:
        for line in fin:
            word = line.strip()
            extentDict[word] = 1.5
    with open(dir + "1.25" + "倍.txt", "r", encoding="utf-8") as fin:
        for line in fin:
            word = line.strip()
            extentDict[word] = 1.25
    with open(dir + "2" + "倍.txt", "r", encoding="utf-8") as fin:
        for line in fin:
            word = line.strip()
            extentDict[word] = 2
    return extentDict


# load
postDict = loadDict("./res/正面情绪词.txt", 1)  # 积极情感词典
negDict = loadDict("./res/负面情绪词.txt", -1)  # 消极情感词典
inverseDict = loadDict("./res/否定词.txt", -1)  # 否定词词典
extentDict = loadExtentDict("./res/")
punc = loadDict("./res/chineseStoputf8.txt", 1)
exclamation = {"!": 2, "！": 2}


def getScore(content):
    words = jieba.cut(content)
    wordList = list(words)
    # print(wordList)

    totalScore = 0  # 记录最终情感得分
    lastWordPos = 0  # 记录情感词的位置
    lastPuncPos = 0  # 记录标点符号的位置
    i = 0  # 记录扫描到的词的位置

    for word in wordList:
        if word in punc:
            lastPuncPos = i

        if word in postDict:
            if lastWordPos > lastPuncPos:
                start = lastWordPos
            else:
                start = lastPuncPos

            score = 1
            for word_before in wordList[start:i]:
                if word_before in extentDict:
                    score = score * extentDict[word_before]
                if word_before in inverseDict:
                    score = score * -1
            for word_after in wordList[i + 1 :]:
                if word_after in punc:
                    if word_after in exclamation:
                        score = score + 2
                    else:
                        break
            lastWordPos = i
            totalScore += score
        elif word in negDict:
            if lastWordPos > lastPuncPos:
                start = lastWordPos
            else:
                start = lastPuncPos
            score = -1
            for word_before in wordList[start:i]:
                if word_before in extentDict:
                    score = score * extentDict[word_before]
                if word_before in inverseDict:
                    score = score * -1
            for word_after in wordList[i + 1 :]:
                if word_after in punc:
                    if word_after in exclamation:
                        score = score - 2
                    else:
                        break
            lastWordPos = i
            totalScore += score
        i = i + 1

    return totalScore


from time import sleep
import random

# Method 2
urlList = [
    "https://movie.douban.com/subject/25845392/",
    "https://movie.douban.com/subject/26363254/",
    "https://movie.douban.com/subject/34841067/",
    "https://movie.douban.com/subject/26794435/",
    "https://movie.douban.com/subject/35267208/",
    "https://movie.douban.com/subject/35766491/",
    "https://movie.douban.com/subject/27619748/",
    "https://movie.douban.com/subject/26100958/",
    "https://movie.douban.com/subject/35613853/",
    "https://movie.douban.com/subject/35267208/",
]
for url in urlList:
    tempDateList = list()
    tempIPList = list()
    tempFilmList = list()
    tempscoreList = list()
    idx = 0
    try:
        for t, d, l, f in getLongReview(url):
            idx += 1
            tempDateList.append(d)
            tempIPList.append(l)
            tempFilmList.append(f)
            tempscoreList.append(getScore(t))
    except BaseException:
        print(url, "出现问题,已经爬取了", idx)
    finally:
        UserListDate.append(tempDateList)
        UserListIP.append(tempIPList)
        UserListFilmNum.append(tempFilmList)
        m2score.append(tempscoreList)
import pickle


class fileobj:
    def __init__(self, dd, ii, ff, ss) -> None:
        self.dd = dd
        self.ii = ii
        self.ff = ff
        self.ss = ss


objj = fileobj(UserListDate, UserListIP, UserListFilmNum, m2score)
with open("./data/mydata.plk", "wb") as f:
    pickle.dump(objj, f)
