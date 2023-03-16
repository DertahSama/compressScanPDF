import fitz,os,shutil,cv2,img2pdf,sys,time,glob
from PIL import Image
from tkinter import filedialog

def ProgressBar(now,alls):
    print("\r", end="")
    progress=int(now/alls*50)
    print("进度: %d/%d: "%(now,alls), "▋"*progress + "-"*(50-progress), end="")
    sys.stdout.flush()
    time.sleep(0.01)

def toColor(file_name,set_quality):
    imgdata=Image.open("./RAW/"+file_name)
    set_width=1200
    im_resized=imgdata.resize((set_width,int(set_width*imgdata.height/imgdata.width)))
    dpi_set=im_resized.width/7.09  #固定页面宽度为18cm（7.09inch）的话，dpi应该就是img.width/7.09
    im_resized.save("./RAW/alter/"+file_name, optimize=True, quality=set_quality,subsampling=2, dpi=(dpi_set,dpi_set))

def toBW(file_name):
    img_cv=cv2.imread("./RAW/"+file_name)
    height, width, channels = img_cv.shape
    if width<3000:
        img_cv=cv2.resize(img_cv,(3000,round(height*3000/width)),interpolation=cv2.INTER_LANCZOS4)
    # 二值化
    # blurred = cv2.GaussianBlur(img_cv, (1, 1), 0) #涂抹降噪，不想涂抹的话改成(1,1)
    gray=cv2.cvtColor(img_cv ,cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 81, 30)
    # cv2.imwrite("./RAW/alter/%04d.png"%(current_page+1),binary,[cv2.IMWRITE_PNG_BILEVEL, 1, int(cv2.IMWRITE_PNG_COMPRESSION),9])#,(int(cv2.IMWRITE_TIFF_COMPRESSION),32766))
    # cv2.imwrite("./RAW/alter/%04d.tiff"%(current_page+1),binary,[cv2.IMWRITE_TIFF_COMPRESSION,4])#,(int(cv2.IMWRITE_TIFF_COMPRESSION),32766))
    img_pil=Image.fromarray(binary)
    imgdata=img_pil.convert('1')
    # imgdata.save("./RAW/alter/%04d.png"%(current_page+1))
    dpi_set=imgdata.width/7.09  #固定页面宽度为18cm（7.09inch）的话，dpi应该就是img.width/7.09
    imgdata.save("./RAW/alter/"+file_name+".tiff", format="TIFF", compression="group4",dpi=(dpi_set,dpi_set))

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

def main():
    print("这是一个用来压缩【【影印】】PDF的简易脚本。转黑白的压缩效果比较好。——wyx230315")
    while 1:
        print("打开文件……")
        f_path = filedialog.askopenfilename(initialdir='./',filetypes=(('PDF files','*.pdf'),))
        if not f_path:
            exit()
        pdf_in=fitz.open(f_path)

        if os.path.exists('./RAW'):    #清空存下载数据的RAW文件夹
            shutil.rmtree('./RAW')
        os.mkdir('./RAW')
        os.mkdir('./RAW/alter')
        
        print("抽取图片中……")
        for current_page in range(len(pdf_in)):
            page = pdf_in.load_page(current_page)
            page_width=page.rect.width  # in px, 1px = 1/72 inch
            pix=page.get_pixmap(dpi=int(2000*72/page_width)) # 输出图片横向像素2000
            pix.save("./RAW/"+"%04d.jpg"%(current_page+1))
            ProgressBar(current_page+1,len(pdf_in))

        print("\n压缩模式选择：")
        print("【1】全黑白（或直接回车）；\n【2】保留原色；\n【3】指定几页保留原色。")
        mode=input("按键选择……")

        if mode=='1':
            pass
        elif mode=='2':
            myquality=50
        elif mode=='3':
            myquality=60
            print("下面指定要保留原色的页数，总页数为：%d"%(len(pdf_in)))
            the_pages_raw=input("输入要保留原色的页码（举例，「1-3,15,20-22」表示[1,2,3,15,20,21,22]这些页）：")
            the_pages=getPages(the_pages_raw)
        else:
            print("默认选为全黑白。")
            mode='1'

        for current_page in range(len(pdf_in)):
            file_name="%04d.jpg"%(current_page+1)
            if mode=='1':
                toBW(file_name)
            elif mode=='2':
                toColor(file_name,myquality)
            elif mode=='3':
                if current_page+1 in the_pages:
                    toColor(file_name,myquality)
                else:
                    toBW(file_name)

            ProgressBar(current_page+1,len(pdf_in))
            
        print("\n合成……",end='')
        (a,f_path)=os.path.split(f_path)
        new_file=a+"/[压缩]"+f_path
        with open(new_file, "wb") as f:
            f.write(img2pdf.convert(glob.glob("./RAW/alter/*.*")))
        print("已保存到："+new_file)
        new_file1=new_file.replace('/','\\')
        os.system(f"C:\Windows\explorer.exe /select, {new_file1}")

        input("\n按回车键再处理一份……")

if __name__=="__main__":
    main()

