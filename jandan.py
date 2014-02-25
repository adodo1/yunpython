#!/usr/bin/env python3
#coding: utf-8
import smtplib, sys, os, re, urllib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.Header import Header

sender = 'sender@126.com'
receiver = 'to@126.com'
subject = 'python email'
smtpserver = 'smtp.126.com'
username = 'username'
password = 'password'
savepath = './img'

reload(sys)
sys.setdefaultencoding('utf-8')

'''
<li class="row" id="comment-2334959">
<b>幼儿园小蘑菇</b> <span class="time"><a href="#respond" title="@回复" onclick="document.getElementById('comment').value += &#39;@&lt;a href=&quot;http://jandan.net/pic/page-4145#comment-2334959&quot;&gt;幼儿园小蘑菇&lt;/a&gt;: &#39;">@ 7 hours ago</a></span><span class="righttext"><a href="http://jandan.net/pic/page-4145#comment-2334959">#103611</a>
 <iframe marginheight="0" src="http://hits.sinajs.cn/A1/weiboshare.html?type=3&amp;count=0&amp;showbutton=1&amp;pic=http://ww4.sinaimg.cn/mw600/61fecdffjw1edtokd093xg206p05wnpb.gif&amp;title=【无聊图】103610楼&amp;url=http://jandan.net/pic/page-4145#comment-2334959&amp;language=zh_cn&amp;appkey=43259970" frameborder="0" height="16" scrolling="no" width="16"></iframe></span>
<p>这个有人敢坐么<br />
<img src="http://ww4.sinaimg.cn/mw600/61fecdffjw1edtokd093xg206p05wnpb.gif" /></p>
<div class="vote" id="vote-2334959"><span id="acv_stat_2334959"></span><a title="圈圈/支持" class="acvclick acv4" id="vote4-2334959" href="javascript:acv_vote(2334959,1);">oo</a> [<span id="cos_support-2334959">6</span>] <a title="叉叉/反对" class="acvclick acva"  id="votea-2334959"  href="javascript:acv_vote(2334959,0);">xx</a> [<span id="cos_unsupport-2334959">14</span>]</div>
</li>
'''

def readjandan(url):
    #html = urllib.urlopen(url).read().decode('utf-8')
    html = urllib.urlopen(url).read()
    # 先解析出当前是第几页 <span class="current-comment-page">[页数]</span>
    match_page = re.search(r'"current-comment-page">\[(?P<page>.*?)\]</span>', html, re.I)
    page = match_page.group('page')
    print 'page=' + page
    
    # 每一页创建一个目录
    imagedir = os.path.join(savepath, page)
    if os.path.exists(imagedir) == False:
        os.mkdir(imagedir)
    
    # 解析楼层
    result = []
    num = 0
    rc_html = re.compile(r'<li class="row" id="comment-[\s\S]*?</li>', re.I)
    for mach_html in rc_html.finditer(html):
        # <li class="row" id="comment-楼层">
        # >@时间</span>
        # <a href="LINK">#
        # <p>(文字描述)*(<img src="图片" />)*</p>
        # 解析每层楼的内容，每层里可能包含多张图片和多段文字
        echofloor = mach_html.group(0)
        pattern = r'<li class="row" id="comment-(?P<floor>.*?)">[\s\S]*?'   \
                   '>@(?P<time>.*?)</span>[\s\S]*?'                         \
                   '<a href="(?P<link>.*?)">#[\s\S]*?'                      \
                   '<p>(?P<context>[\s\S]*?)<div class="vote"'              \
                   '[\s\S]*?</li>'
        rc_floor = re.compile(pattern)

        for mach_floor in rc_floor.finditer(echofloor):
            '''
            print 'floor=' + mach_floor.group('floor')
            print 'time=' + mach_floor.group('time')
            print 'link=' + mach_floor.group('link')
            print 'context=<p>' + mach_floor.group('context').strip()
            print '------------------------------------'
            '''
            num += 1
            floor = mach_floor.group('floor')
            time = mach_floor.group('time')
            link = mach_floor.group('link')
            context = '<p>' + mach_floor.group('context').strip()
            # 解析出context中的每张图片地址，下载下来并重新指向context中的图片地址
            index = 0
            rc_image = re.compile('<img src="(?P<image>.*?)"')
            for mach_image in rc_image.finditer(context):
                index += 1
                image = mach_image.group('image')
                newimage = os.path.join(imagedir, floor + str(index))
                if os.path.exists(newimage) == False:
                    print 'downing page:{0} floor:({1},{2}) img:{3} ... '.format(page, num, floor, image),
                    try:
                        urllib.urlretrieve(image, newimage)         # 下载图片放在临时目录
                        print 'OK'
                    except Exception as ex:
                        print 'Fail'
                context = context.replace(image, newimage)          # 替换url
            
            comment = readcomment(floor)                            # 读取评论
            dict = {'floor':floor, 'time':time, 'link':link, 'context':context, 'comment':comment}
            result.append(dict)
    return (page, result)

def readcomment(floor):
    try:
        # 读取吐槽信息
        #http://jandan.duoshuo.com/api/threads/listPosts.json?thread_key=comment-2116138
        url = r'http://jandan.duoshuo.com/api/threads/listPosts.json?thread_key=comment-%s' % floor
        print 'Reading comment: %s .... ' % url,
        html = urllib.urlopen(url).read().decode('utf-8')
        print 'OK'

        result = '<DIV style="cursor:hand" onclick="isHidden(\'div{0}\')"><font color="red">评论</font></DIV>'.format(floor)
        result += '<DIV id="div{0}" style="display:none">'.format(floor)
        html = html.replace(r'\"', r'\'').replace(r'\/', r'/').replace(r"\'", r"'").replace(r'\r\n', ' ')
        #HTML的&lt;&gt;&amp;&quot;&copy;对别是<，>，&，"，©;的转义字符
        html = html.replace(r'&lt;', '<').replace(r'&gt;', '>').replace(r'&amp;', '&').replace(r'&quot;', '\'').replace(r'&copy;', '©')
        rc_comment = re.compile(r'"message":"(?P<message>[\s\S]*?)"[\s\S]*?"likes":(?P<likes>[\s\S]*?),', re.I)
        for mach_comment in rc_comment.finditer(html):
            #print 'likes=' + mach_comment.group('likes'),
            #print 'message=' + mach_comment.group('message')
            result += "顶:{0}, 评论:{1}</br>".format(mach_comment.group('likes'), mach_comment.group('message'))
        result += "</DIV>"
        return result
    except Exception as ex:
        print ex
        return ""
    
    

def buildhtml(infos, page):
    context = '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />' \
    """
      <SCRIPT>
        function isHidden(oDiv){
          var vDiv = document.getElementById(oDiv);
          vDiv.style.display = (vDiv.style.display == 'none')?'block':'none';
        }
      </SCRIPT>
      <style type="text/css">
      div#wrap {
      width:960px;
      margin:0 auto;
      border:1px solid #e9eee3;
      background-color:#f1fedd;
      }
      </style>
      <div id="wrap">
    """
    for info in infos:
        context += '<a href="{0}" target="_blank">{1}</a>{2}{3}</br>{4}<hr>\r\n'.format(info['link'], info['floor'], info['time'], info['context'], info['comment'])
    context += "</div>"
    
    file_object = open(str(page) + '.html', 'w')
    file_object.write(context)
    file_object.close( )
    
def readhtml(url):
    html = urllib.urlopen(url).read().decode('utf-8');
    # 先解析出当前是第几页 <span class="current-comment-page">[页数]</span>
    match_page = re.search(r'"current-comment-page">\[(?P<page>.*?)\]</span>', html, re.I)
    page = match_page.group('page')
    print 'page=' + page
    result = []
    # 解析页面中 时间,楼层,LINK,文字描述,图片
    # <li id="comment-楼层">
    # @</a>时间</span>
    # <a href="LINK">#
    # <p>文字描述<img
    # <img src="图片" />
    rc_context = re.compile(r'<li id="comment-(?P<floor>.*?)">[\s\S]*?@</a>(?P<time>.*?)</span>[\s\S]*?<a href="(?P<link>.*?)">#[\s\S]*?<p>(?P<text>[\s\S]*?)<img src="(?P<image>.*?)"[\s\S]*?</li>', re.I)
    for mach_context in rc_context.finditer(html):

        print 'floor=' + mach_context.group('floor')
        print 'time=' + mach_context.group('time')
        print 'link=' + mach_context.group('link')
        print 'text=<p>' + mach_context.group('text').strip()
        print 'image=' +  mach_context.group('image').strip()
        print '------------------------------------'


        floor = mach_context.group('floor')
        time = mach_context.group('time')
        link = mach_context.group('link')
        text = '<p>' + mach_context.group('text').strip()
        image = mach_context.group('image').strip()
        

        
        #imageName = image[image.rindex('/')+1:]
        #imageName = floor + imageName[imageName.rindex(".")+1:]
        #print '>> ' + imageName[imageName.rindex('.')+1:]
        #urllib.urlretrieve(image, os.path.join(savepath, floor))    # 下载图片放在临时目录
        dict = {'floor':floor, 'time':time, 'link':link, 'text':text}
        result.append(dict)
        print floor
    return result
        
def buildmail(infos):
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = Header('煎蛋-无聊图', 'utf-8')
    context = ''
    for info in infos:
        context += '<a href="{0}">{1}</a>{2}{3}<br><img src="cid:{4}"><hr>'.format(info['link'], info['floor'], info['time'], info['text'], info['floor'])
        # 添加附件
        fp = open(os.path.join(savepath, info['floor']), 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        msgImage.add_header('Content-ID', '<{0}>'.format(info['floor']))
        msgRoot.attach(msgImage)
    msgRoot.attach(MIMEText(context, _subtype='html', _charset='utf-8'))
    return msgRoot
    
if __name__=='__main__':
    if not os.path.exists(savepath) :
        os.mkdir(savepath)

    if len(sys.argv) == 2:
        (page, result) = readjandan(r'http://jandan.net/pic/page-%s' % sys.argv[1])
        buildhtml(result, page)
    else:
        print '--------------------'
        (page, result) = readjandan(r'http://jandan.net/pic')
        buildhtml(result, page)
        (page, result) = readjandan(r'http://jandan.net/pic/page-{0}'.format(int(page) - 1))
        buildhtml(result, page)
        (page, result) = readjandan(r'http://jandan.net/pic/page-{0}'.format(int(page) - 1))
        buildhtml(result, page)
        (page, result) = readjandan(r'http://jandan.net/pic/page-{0}'.format(int(page) - 1))
        buildhtml(result, page)
        (page, result) = readjandan(r'http://jandan.net/pic/page-{0}'.format(int(page) - 1))
        buildhtml(result, page)
        (page, result) = readjandan(r'http://jandan.net/pic/page-{0}'.format(int(page) - 1))
        buildhtml(result, page)
    '''
    mailbody = buildmail(result)
    smtp = smtplib.SMTP()
    smtp.connect(smtpserver)
    smtp.login(username, password)
    smtp.sendmail(sender, receiver, mailbody.as_string())
    smtp.quit()
    '''
    print 'OK'
    

'''
msgRoot = MIMEMultipart('related')
msgRoot['Subject'] = 'test message'

msgText = MIMEText('<b>Some <i>HTML</i> text</b> and an image.<br><img src="cid:image1"><br>good!','html','utf-8')
msgRoot.attach(msgText)

fp = open('c:\\temp\\test.gif', 'rb')
msgImage = MIMEImage(fp.read())
fp.close()
print 'START'
msgImage.add_header('Content-ID', '<image1>')
msgRoot.attach(msgImage)
smtp = smtplib.SMTP()
smtp.connect('smtp.126.com')
print 'CONNECT OK'
smtp.login(username, password)
print 'LOGIN OK'
smtp.sendmail(sender, receiver, msgRoot.as_string())
smtp.quit()
print 'FINISH'
'''
