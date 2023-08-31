# (c) 2022/11/13 yoya@awn.jp

import os, sys, time
import json
from urllib import parse
import shutil
from TwiAgentBookmark import TwiAgentBookmark
from util import imgcat, youtubeDl

prog, profileName = sys.argv;

def url_to_origurl_filename(src, fmt = None):
    up = parse.urlparse(src)
    qs = parse.parse_qs(up.query)
    if fmt is None:
        fmt = qs['format'][0]
#    url = "{}://{}{}?format={}&name=orig".format(up.scheme, up.netloc, up.path, fmt)
    url = "{}://{}{}?format={}&name=4096x4096".format(up.scheme, up.netloc, up.path, fmt)
    filename = "{}.{}".format(up.path.split('/')[-1], fmt);
    return [url, filename]

# setup

os.makedirs("media", exist_ok=True)
logf = open("tweet.txt", 'a')

def main(agent, retry):
    articles = agent.readBookmarkArticleList()
    articlesLen = len(articles)
#    print("articles count:{}".format(articlesLen))
    if (articlesLen < 1):
        agent.loadArticle()
        return False  # soft error
    for article in articles:
        url, text, imgsrcs, video = agent.readBookmarkArticle(article)
        print(url, "imgsrcs len:{}".format(len(imgsrcs)))
        logf.write("========\n{}\n{}\n{}\n\n".format(url, text, imgsrcs))
        imgsrcsLen = len(imgsrcs)
#        print("    imgsrcs count:{}".format(imgsrcsLen))
        found = False
        for src in imgsrcs:
            dlDone = False;  # download したフラグ
            for f in ["png", "jpg", "webp", None]:
                imgurl, imgfile = url_to_origurl_filename(src, f)
                imgfile = "media/{}".format(imgfile)
                if os.path.isfile(imgfile):
                    print("found")
                    dlDone = False;  # 手元にファイルがあるので DL しない
                    break
                try:
                    img = agent.downloadPhotoImage(imgurl)
                    dlDone = True
                    break
                except Exception as e:
                    dlDone = False;  # D/L 失敗
            if dlDone is False:
                continue
            with open(imgfile, 'wb') as f:
                shutil.copyfileobj(img, f)
                print(imgurl)
                if os.environ["TERM_PROGRAM"] == "iTerm.app":
                    imgcat(imgfile, 10)
                    time.sleep(2)
                    if video:
                        videoId = url.split("/")[-1]
                        print("url, videoId:", url, videoId)
                        youtubeDl(url, "media/{}.mp4".format(videoId))
        if found == False or True:
            agent.removeBookmarkArticle(article)
            time.sleep(2)
    return True

agent = TwiAgentBookmark()
agent.openBookmark(profileName)

retry = 0
while (retry < 3):  # 仏の顔も三度まで
    try:
        if main(agent, retry) == True:
            retry = 0
            time.sleep(3)
        else:
            retry = retry + 1
            time.sleep(5)
    except (agent.RetryException) as e:
        agent.refresh()
        time.sleep(5)
        retry = retry + 1  # soft error
        continue
    except (agent.FinishExceptions) as e:
#        print(sys.exception_info())
#        print(e, file=sys.stderr)
        print("OK")
        break
    except Exception as e:
#        print(sys.exception_info())
        print(e, file=sys.stderr)
        print("Retry")
        agent.refresh()
        retry = retry + 1  # soft error
        time.sleep(10)
        continue
    except (agent.AbortExceptions) as e:
        print(sys.exception_info())
        print(e, file=sys.stderr)
        print("Abort")
        break
