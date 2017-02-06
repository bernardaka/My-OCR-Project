from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk,ImageDraw
from skimage import filters
import random
import os
import subprocess

#Image segmentation
#X-axis projection of image，if has data(black pixel) the value seted to 1 otherwise 0
def get_projection_x(image):
    p_x = [0 for x in range(image.size[0])]
    for h in range(image.size[1]):
        for w in range(image.size[0]):
            if image.getpixel((w,h)) == 0:
                p_x[w] = 1
    return p_x

#Get X-axis point after segmentation
#result is a list of start location and length
def get_split_seq(projection_x):
    res = []
    for idx in range(len(projection_x) - 1):
        p1 = projection_x[idx]
        p2 = projection_x[idx + 1]
        if p1 == 1 and idx == 0:
            res.append([idx, 1])
        elif p1 == 0 and p2 == 0:
            continue
        elif p1 == 1 and p2 == 1:
            res[-1][1] += 1
        elif p1 == 0 and p2 == 1:
            res.append([idx + 1, 1])
        elif p1 == 1 and p2 == 0:
            continue
    return res

#The image after segmentation
def split_image(image, split_seq=None):
    if split_seq is None:
        split_seq = get_split_seq(get_projection_x(image))
    length = len(split_seq)
    imgs = [[] for i in range(length)]
    res = []
    for w in range(image.size[1]):
        line = [image.getpixel((h,w)) for h in range(image.size[0])]
        for idx in range(length):
            pos = split_seq[idx][0]
            llen = split_seq[idx][1]
            l = line[pos:pos+llen]
            imgs[idx].append(l)
    for idx in range(length):
        datas = []
        height = 0
        for data in imgs[idx]:
            flag = False
            for d in data:
                if d == 0:
                    flag = True
            if flag == True:
                height += 1
                datas += data
        child_img = Image.new('L',(split_seq[idx][1], height))
        child_img.putdata(datas)
        res.append(child_img)
    return res

def image_to_string(img, cleanup=True, plus=''):
    # Delete txt file when cleanup equal to True
    subprocess.check_output('tesseract ' + img + ' ' +
                            img + ' ' + plus, shell=True)  # generate TXT file
    text = ''
    with open(img + '.txt', 'r') as f:
        text = f.read().strip()
    if cleanup:
        os.remove(img + '.txt')
    return text


#show the image in a label
def showimg(img):
    photo = ImageTk.PhotoImage(img)
    label = Label(disframe,image=photo)
    label.image = photo # keep a reference!
    label.pack()

#open folder and select image
def openimage():
    global myimage
    #clear the frame and text first
    for widget in disframe.winfo_children():
        widget.destroy()
    myimage =Image.open(filedialog.askopenfile(parent=root,mode='rb',title='Select a file'))
    showimg(myimage)

#remove noise
def noiseremove():
    global myimage
    global imgry
    imgry = myimage.convert('L')
    showimg(imgry)

#binarization
def binary():
    global imgry
    global num
    global binaimg
    global result
    threshold = filters.threshold_li(imgry)
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)
    out = imgry.point(table, '1')
    #out.show()
    num = random.randint(1,65535)
    out.save("%s.jpg"%num)
    binaimg =Image.open("%s.jpg"%num)
    showimg(binaimg)
    result = image_to_string("%s.jpg"%num)

#segmentation
def segment():
    a=split_image(binaimg)
    for i in range(len(a)):
        showimg(a[i].resize((15,15)))

#recognation
def recog():
    print(result)

#print out
def printout():
    for widget in resultframe.winfo_children():
        widget.destroy()
    re_text = Text(resultframe,height=20,width=70)
    re_text.insert(END,"%s"%result)
    re_text.pack(side = BOTTOM)

#save as TXT
def savetxt():
    print(num)
    result = image_to_string("%s.jpg"%num,False)
    save_text = Text(resultframe,height=20,width=70)
    save_text.insert(END,"Saved in %s.jpg.txt."%num)
    save_text.pack(side = BOTTOM)
# exit system
def exit():
    global root
    root.destroy()

def guide():
    global text
    text.delete('1.0', END)
    text.insert(END,"1. Select file and import to system.")
    text.insert(END,'\n')
    text.insert(END,'2. Preprocess the corresponding file.')
    text.insert(END,'\n')
    text.insert(END,'3. Do recognition')
    text.insert(END,'\n')
    text.insert(END,'4. You may print out characters or save as TXT.')

#Set a canvas for draw
class WordGenerator:
    def __init__(self,parent,posx,posy,*kwargs):
        self.parent = parent
        self.posx = posx
        self.posy = posy
        self.sizex = 100
        self.sizey = 100
        self.b1 = "up"
        self.xold = None
        self.yold = None
        self.drawing_area=Canvas(self.parent,width=self.sizex,height=self.sizey)
        self.drawing_area.place(x=self.posx,y=self.posy)
        self.drawing_area.bind("<Motion>", self.motion)
        self.drawing_area.bind("<ButtonPress-1>", self.b1down)
        self.drawing_area.bind("<ButtonRelease-1>", self.b1up)
        self.button=Button(self.parent,text="Done!",width=5,bg='white',command=self.save)
        self.button.place(x=self.sizex/7,y=self.sizey+160)
        self.button1=Button(self.parent,text="Clear!",width=5,bg='white',command=self.clear)
        self.button1.place(x=(self.sizex/7)+90,y=self.sizey+160)

        self.image=Image.new("RGB",(100,100),(255,255,255))
        self.draw=ImageDraw.Draw(self.image)

    def save(self):
        filename = "temp.jpg"
        self.image.save(filename)

    def clear(self):
        self.drawing_area.delete("all")
        self.image=Image.new("RGB",(100,100),(255,255,255))
        self.draw=ImageDraw.Draw(self.image)

    def b1down(self,event):
        self.b1 = "down"

    def b1up(self,event):
        self.b1 = "up"
        self.xold = None
        self.yold = None

    def motion(self,event):
        if self.b1 == "down":
            if self.xold is not None and self.yold is not None:
                event.widget.create_line(self.xold,self.yold,event.x,event.y,smooth='true',width=3,fill='black')
                self.draw.line(((self.xold,self.yold),(event.x,event.y)),(0,0,0),width=3)

        self.xold = event.x
        self.yold = event.y

#call drawing canvas
def drawimage():
    WordGenerator(root,50,150)


root = Tk()
root.title("OCR System")

#create menubar
menubar = Menu(root)
root.config(menu=menubar)

filemenu = Menu(menubar)
menubar.add_cascade(label='File',menu=filemenu)
filemenu.add_command(label="Open File", command=openimage)
filemenu.add_command(label="Write", command=drawimage)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=exit)


operamenu = Menu(menubar)
menubar.add_cascade(label="Operation", menu=operamenu)
submenu = Menu(operamenu)
operamenu.add_cascade(label="Preprocess", menu=submenu)
submenu.add_command(label="Noise Removal", command=noiseremove)
submenu.add_command(label="Binarization", command=binary)
submenu.add_command(label="Segmentation", command=segment)

operamenu.add_command(label="Recognize", command=recog)

exportmenu = Menu(menubar)
menubar.add_cascade(label="Export", menu=exportmenu)
exportmenu.add_command(label="Print Out", command=printout)
exportmenu.add_command(label="Save as TXT", command=savetxt)

helpmenu = Menu(menubar)
menubar.add_cascade(label="Help", menu=helpmenu)
helpmenu.add_command(label="Guide", command=guide)

# create toolbar

toolbar = Frame(root)
toolbar.grid(row=0,sticky=W)

new = PhotoImage(file='new.gif')
draw = PhotoImage(file='draw.gif')
recog = PhotoImage(file='recog.gif')
save = PhotoImage(file='save.gif')
convet = PhotoImage(file='convert.gif')

newbutt = Button(toolbar,image=new,command=openimage)
newbutt.grid(row=0)
drawbutt = Button(toolbar,image=draw,command=drawimage)
drawbutt.grid(row=0,column=1)
recogbutt = Button(toolbar,image=recog,command=recog)
recogbutt.grid(row=0,column=2)
savebutt = Button(toolbar,image=save,command=savetxt)
savebutt.grid(row=0,column=3)

#create frame for display and result

dislabel = Label(root,text='Show Image')
dislabel.grid(row=1,sticky=W)
#global disframe
disframe = Frame(root,height=150,width=200,bd=2,relief=SUNKEN)
disframe.grid(row=2,sticky=W)

RESlabel = Label(text='Result')
RESlabel.grid(row=1,column=1,sticky=W)

resultframe = Frame(root,height=150,width=200,bd=2,relief=SUNKEN)
resultframe.grid(row=2,column=1,sticky=E)
global text
text = Text(resultframe,height=20,width=70)
text.insert(END,"Please preprocess first.")
text.pack(side = BOTTOM)

#display
root.mainloop()
