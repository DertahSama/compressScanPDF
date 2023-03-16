这是一个用来压缩扫描出的PDF文档的python小脚本。压缩成纯黑白（1bit色深）的效果最好。
![Snipaste_2023-03-16_20-24-01](https://user-images.githubusercontent.com/74524914/225616311-c59e8800-59c8-440f-9087-6a9c5bf74d4e.jpg)

>这里权作自己的思路笔记了~

## 方法

用`fitz`包打开PDF并提取每页的图片，然后用`PIL`和/或`cv2`包处理图片，然后用`img2pdf`包重新合成成pdf。属实是十分trivial的功能。

### 提取图片

有两种方法：一种是直接用`.get_page_images()`得到pdf内部的原始图片数据并直接输出，该命令得到的是一个记录了每张图片的信息的数组，每条信息也是一个数组，其首个元素就是该图片的引用号`xref`，通过该引用号即可从pdf文件中调取出原始图片。如果每页只是纯粹的一张图片的话是最好的，但是如果不是（例如，用某些手机app生成的扫描pdf会加上水印、二维码之类的）就会掉出一大堆图片，难以处理：
```python
def extract_pic1(pdf_in,current_page):
    for img in pdf_in.get_page_images(current_page):
        xref=img[0]
        fitz.Pixmap(pdf_in, xref).save("./RAW/%04d.png"%(current_page+1))
```
另一种方法就是用`.get_pixmap()`把整个页面转化为图片，这样虽然损失了图片的原始信息，但是是万无一失的。可以通过控制dpi来控制生成的图片的大小，比如下面控制为宽度2000：
```python
def extract_pic2(pdf_in,current_page):
    page = pdf_in.load_page(current_page)
    page_width = page.rect.width  # in px, 1px = 1/72 inch
    page.get_pixmap(dpi=int(2000*72/page_width)).save("./RAW/"+"%04d.png"%(current_page+1))
```

### 压缩成纯黑白

这里要用到`PIL`和`cv2`包两个包的功能：
1. `cv2`包里有一个非常好用的功能：动态阈值`cv2.adaptiveThreshold()`，也就是在二值化的时候，是将图片划定为许多个小方格，在每个小方格里单独确定阈值，使每个小方格里黑:白比例最接近于1。这样可以有效避免在转纯黑白时，画面出现大片死黑/死白的情形，并且也无需费心手动调节阈值了。
2. 纯黑白的图片用tiff格式、CCITT group 4压缩方法储存的压缩效率最高，一张10M像素的黑白扫描图仅需几十kB，用`PIL`包这样保存最方便，注意提前将色域转为1 bit。

另外，鉴于转纯黑白时字体边缘的过渡将变得十分生硬，所以宜在转换前适当放大图片，最终文件大小只会有很小的变大。
```python
def toBW(file_name):
    img_cv=cv2.imread("./RAW/"+file_name)
    height, width, channels = img_cv.shape
    if width<3000:
        img_cv=cv2.resize(img_cv,(3000,round(height*3000/width)),interpolation=cv2.INTER_LANCZOS4) # 放大到宽度3000
   
    gray=cv2.cvtColor(img_cv ,cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 81, 30) # 二值化

    img_pil=Image.fromarray(binary) # 从cv2的格式转到PIL的格式
    imgdata=img_pil.convert('1') # 色域转为1 bit
    dpi_set=imgdata.width/7.09  #固定页面宽度为18cm（7.09inch）的话，dpi应该就是img.width/7.09
    
    imgdata.save("./RAW/alter/"+file_name+".tiff", format="TIFF", compression="group4",dpi=(dpi_set,dpi_set))
```

### 压缩彩色

没什么好说的，用jpg格式，设一个较低的`quality`、降采样到`4:2:0`即可。另外之前输出图片的时候把页面图片宽度控制为了2000，这是偏大的，注意给它降回去，否则达不到压缩的目的。
```python
def toColor(file_name,set_quality):
    imgdata=Image.open("./RAW/"+file_name)
    set_width=1200
    im_resized=imgdata.resize((set_width,int(set_width*imgdata.height/imgdata.width)))
    dpi_set=im_resized.width/7.09  #固定页面宽度为18cm（7.09inch）的话，dpi应该就是img.width/7.09
    
    im_resized.save("./RAW/alter/"+file_name, optimize=True, quality=set_quality,subsampling=2, dpi=(dpi_set,dpi_set))
```

### 合成pdf
`img2pdf`包操作是最方便的，压缩效率也是最高的：
```python
with open(new_file, "wb") as f:
    f.write(img2pdf.convert(glob.glob("./RAW/alter/*.*")))
```
但是这个包在处理tiff文件时候每个文件都会弹出一行提示，几百行很烦人！我之前改了该包的源代码把这个提示干掉了，但是现在忘了在哪里改的了，等我记起来了再在这里记录罢。

### 选页
压缩pdf的时候会出现只选取一些页面保留彩色、其它页面变纯黑白的情况。这里仿照通用的选页语法写了个小函数，可以将输入的形如
> 1-3,15,20-22

的文本转化为页码数组
```
[1,2,3,15,20,21,22]
```
用了两次`.split()`方法而已：
```python
def getPages(str):
    pages_cache=str.split(',')
    the_pages=[]
    for item in pages_cache:
        item_cache=item.split('-')
        if len(item_cache)==2: # 此时item_cache形如['20','22']
            the_pages.extend(range(int(item_cache[0]),int(item_cache[1])+1))
        else: # 此时item_cache形如['15']
            the_pages.append(int(item_cache[0]))
    return the_pages
```
