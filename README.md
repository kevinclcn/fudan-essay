# 复旦大学论文下载

## 使用方法
1. 安装python依赖
```bash
pip install -r requirements.txt
```
2. 打开vpn，登录 https://thesis.fudan.edu.cn/
3. 搜索论文，点击查看全文，在浏览器地址栏中找到fid=后面的字符串，保存备用
4. 打开浏览器开发者工具，点击应用标签，点击Cookie菜单，找到JSessionID，保存备用
5. 运行程序
```bash
python crawl_mba_essay.py <JSessionID> <fid> [filename]
```
注意：
1. <JSessionID> 是复旦大学论文下载系统的JSessionID，可以在浏览器中查看
2. <fid> 是论文的文件ID，可以在浏览器地址栏中fid=后面的字符串
3. [filename] 是论文的文件名，如果未提供，则使用 <fid> 作为文件名

比如：
```bash
python crawl_mba_essay.py ABC123XYZ 12345 my_thesis
```
则会在当前目录下生成一个名为my_thesis的PDF文件

