'''
  function:爬取j-stage（支援対話研究）杂志论文，并写入Excel文件
  env:python3.6.5
  author:lmx
'''
import time
import requests

from openpyxl import workbook  # 写入Excel表所用
from bs4 import BeautifulSoup as bs
class Jstage:
    def __init__(self):
        #起始地址
        self.start_url = 'https://www.jstage.jst.go.jp/browse/jadcs/' # url前半部分不变，只需修改最后数字
        #请求头，浏览器模拟
        self.headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        }
        # 本卷有多少号
        self.page_num = 6

    '''url拼接'''
    def get_page_url(self):
        n = 0 #第一页开始,下标0
        while n<self.page_num:
            yield self.start_url+ str(n) + '/0/_contents/-char/ja'
            n += 1

    '''获取页面源码'''
    def getHtml(self):
        gu = self.get_page_url() #url生成器
        for url in gu:
            html = requests.get(url,headers=self.headers).text
            yield html

    '''数据提取'''
    def getData(self):
        gh = self.getHtml() # html源码生成器
        for html in gh: # html:网页源码
            soup = bs(html, 'html.parser')
            #tmp = soup.find_all('ul', class_='search-resultslisting') # 辅助定位
            for ul in soup.find_all('ul', class_='search-resultslisting'):
                for li in ul.find_all('li'):
                    # 标题
                    title = li.find('div',class_='searchlist-title').text.strip()
                    # 找到标题内部的链接，跳转进去
                    title_url = li.find('div', class_='searchlist-title').find('a').get('href')
                    # 将详情页转为html
                    title_html = requests.get(title_url).text
                    soup = bs(title_html, 'html.parser')
                    # 找到作者所在研究机关
                    try:
                        institution = soup.find('ul', class_='accodion_body_ul').find('li').find('p').text.strip()
                        author = soup.find('a', class_='customTooltip').text
                    except:
                        institution = "none"
                        author = "no author"
                    # 查找论文keyword
                    try:
                        pre_keyword = soup.find('div', class_='global-para').text.strip()
                        pre_keyword = pre_keyword.replace('\u2003', '').replace('\u3000', '').replace('\t', '').replace('\n', '').strip()
                    except:
                        pre_keyword = "none:none"

                    # 对keyword进行分割，只留关键信息
                    try:
                        pre_keyword = pre_keyword.split(":",1)
                        pre, keyword = pre_keyword[0],pre_keyword[1]
                    except:
                        keyword = "none"

                    # 在搜索页查找作者名，发表年份，几卷几号，第几页
                    try:
                        #author = li.find('div',class_='searchlist-authortags customTooltip').text.strip()
                        info = li.find('div',class_='searchlist-additional-info').text.strip()
                        info = info.replace('\u2003', '').replace('\u3000', '').replace('\t', '').replace('\n', '').strip()
                        #info = info.split("文",1)
                        #info = info[1]
                        info = info.split("年",1)
                        year, rem = info[0],info[1]
                        rem = rem.split("p.",1)
                        vol, page = rem[0],rem[1]
                        page = page.split("発",1)
                        page = page[0]
                    except:
                        print(title + ",未能收集")
                        #author = "no author"
                        year = "no year"
                        vol = "no vol"
                        page = "no page"

                    # 查找概要
                    try:
                        abstract = li.find('div', class_='inner-content abstract').text.strip()
                        abstract = abstract.replace('\u2003', '').replace('\u3000', '').replace('\t', '').replace('\n', '').strip()
                    except:
                        abstract = "none. 抄録全体を表示"

                    abstract = abstract.split("抄録全体", 1)
                    abstract = abstract[0]

                    # 执行论文pdf下载
                    pre_file_url = li.find('div', class_='lft').find('span').find('a')
                    file_url = pre_file_url.get('href')

                    print(file_url)
                    try:
                        r = requests.get(file_url, stream=True)
                        with open("[" + vol + "]" + page + ".pdf", "wb") as pdf:
                            for chunk in r.iter_content(chunk_size=1024):
                                if chunk:
                                    pdf.write(chunk)
                        print("完成收集:" + title)
                    except Exception as e:
                        print("------------------------------------------------未能下载:" + title)
                        print("原因:%s"%e)

                    # 对服务器仁慈
                    time.sleep(8)
                    yield [author, institution, title, keyword, year, vol, page, abstract]


    '''保存到excel文件
    :param file_name:文件名
    '''
    def saveToExcel(self,file_name):
        wb = workbook.Workbook()  # 创建Excel对象
        ws = wb.active  # 获取当前正在操作的表对象
        ws.append(['author', 'institution', 'title', 'keyword', 'year', 'vol', 'page', 'abstract'])
        gd = self.getData() #数据生成器
        for data in gd:
            ws.append(data)
        wb.save(file_name)

if __name__ == '__main__':
    start = time.time()
    top = Jstage()
    try:
        top.saveToExcel('shientaiwa.xlsx')
        print('抓取成功,用时%4.2f'%(time.time()-start)+'秒')
    except Exception as e:
        print('抓取失败,原因:%s'%e)
