from threading import Timer
import time
import tkinter as tk
import random
import copy                              #使用deepcopy函数拷贝2维数组必须引用copy
#将tile指定的黑或白棋子放到棋盘x行y列方格处，p为相应图像,board是记录棋盘中棋子如何分布的2维列表
import random
import math
import time

BOARD_SIZE = 8
PLAYER_NUM = 'black'
COMPUTER_NUM = 'white'
MAX_THINK_TIME = 60
direction = [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]]

def putPiece(board,x,y,tile,p):           #tile='black'代表黑棋子，tile='white'为白棋子
    board[x][y] = tile       #8*8棋盘x行y列方格处放置由tile指定的黑或白棋子信息保存到2维列表board中
    #将棋子图像p放到由棋盘坐标(x,y)转换为Canvas点阵坐标处。44和45是棋盘边界距Canvas边界的x和Y方向距离
    a=w.create_image((44+x*40),(45+y*40),image=p,tag="p")           #棋盘单元格宽和高都是40  
    allPieces[x,y]=a        #将该图像对象ID保存的字典allPieces
# 开局时建立新棋盘，'none'表示无子，'black'代表黑棋子，'white'为白棋子
def getNewBoard():
    board = []
    for i in range(8):
        board.append(['none'] * 8)
    putPiece(board,3,3,'black',pb)      #在棋盘3行3列方格处放黑棋子
    putPiece(board,3,4,'white',pw)
    putPiece(board,4,3,'white',pw)
    putPiece(board,4,4,'black',pb)
    return board
# 初始化棋盘数组

def getInitialBoard():
    board = {}

    for i in range(0, BOARD_SIZE):
        board[i] = {}

        for j in range(0, BOARD_SIZE):
            board[i][j] = 0

    board[BOARD_SIZE / 2 - 1][BOARD_SIZE / 2 - 1] = COMPUTER_NUM
    board[BOARD_SIZE / 2][BOARD_SIZE / 2] = COMPUTER_NUM

    board[BOARD_SIZE / 2 - 1][BOARD_SIZE / 2] = PLAYER_NUM
    board[BOARD_SIZE / 2][BOARD_SIZE / 2 - 1] = PLAYER_NUM

    return board


# 返回棋子数
def countTile(board, tile):
    stones = 0
    for i in range(8):
        for j in range(8):
            if board[i][j] == tile:
                stones += 1

    return stones
# 获取棋盘上黑白双方的棋子数

def getScoreOfBoard(board):
    xscore = 0
    oscore = 0
    for x in range(8):
        for y in range(8):
            if board[x][y] == 'black':
                xscore += 1
            if board[x][y] == 'white':
                oscore += 1
    return {'black':xscore, 'white':oscore}     #返回字典

# 返回一个颜色棋子可能的下棋位置
def possible_positions(board, tile):
    positions = []
    for i in range(0, BOARD_SIZE):
        for j in range(0, BOARD_SIZE):
            if board[i][j] != 'none':
                continue
            if updateBoard(board, tile, i, j, checkonly=True) > 0:
                positions.append((i, j))
    return positions

def isOnBoard(x, y):
    return x >= 0 and x <= 7 and y >= 0 and y <= 7


# 是否是合法走法，如果合法返回需要翻转的棋子列表
def updateBoard(board, tile, i, j, checkonly=False):
    # 该位置已经有棋子或者出界了，返回False
    reversed_stone = 0

    # 临时将tile 放到指定的位置
    board[i][j] = tile
    if tile == 'black':
        change = 'white'
    else:
        change = 'black'

    # 要被翻转的棋子
    need_turn = []
    for xdirection, ydirection in direction:
        x, y = i, j
        x += xdirection
        y += ydirection
        if isOnBoard(x, y) and board[x][y] == change:
            x += xdirection
            y += ydirection
            if not isOnBoard(x, y):
                continue
            # 一直走到出界或不是对方棋子的位置
            while board[x][y] == change:
                x += xdirection
                y += ydirection
                if not isOnBoard(x, y):
                    break
            # 出界了，则没有棋子要翻转
            if not isOnBoard(x, y):
                continue
            # 是自己的棋子，中间的所有棋子都要翻转
            if board[x][y] == tile:
                while True:
                    x -= xdirection
                    y -= ydirection
                    # 回到了起点则结束
                    if x == i and y == j:
                        break
                    # 需要翻转的棋子
                    need_turn.append([x, y])
    # 将前面临时放上的棋子去掉，即还原棋盘
    board[i][j] = 'none'  # restore the empty space
    # 没有要被翻转的棋子，则走法非法。翻转棋的规则。
    for x, y in need_turn:
        if not (checkonly):
            board[i][j] = tile
            board[x][y] = tile  # 翻转棋子
        reversed_stone += 1
    return reversed_stone


# 蒙特卡洛树搜索
def mctsNextPosition(board):
    def ucb1(node_tuple, t, cval):
        name, nplayout, reward, childrens = node_tuple

        if nplayout == 0:
            nplayout = 0.00000000001

        if t == 0:
            t = 1
        #reward 是赢的次数 nplayout是模拟对局次数,cval是常数
        return (reward / nplayout) + cval * math.sqrt(2 * math.log(t) / nplayout)

    def find_playout(tep_board, tile, depth=0):
        def eval_board(tep_board):
            player_tile = countTile(tep_board, PLAYER_NUM)
            computer_tile = countTile(tep_board, COMPUTER_NUM)
            if computer_tile > player_tile:
                return True
            return False
        if depth > 32:
            return eval_board(tep_board)
        turn_positions = possible_positions(tep_board, tile)

        # 查看是否可以在这个位置下棋
        if len(turn_positions) == 0:
            if tile == COMPUTER_NUM:
                neg_turn = PLAYER_NUM
            else:
                neg_turn = COMPUTER_NUM

            neg_turn_positions = possible_positions(tep_board, neg_turn)

            if len(neg_turn_positions) == 0:
                return eval_board(tep_board)
            else:
                tile = neg_turn
                turn_positions = neg_turn_positions

        # 随机放置一个棋子
        roxanne_table = [
            [[0,0], [0,7], [7,0], [7,7]],
            [[2,2], [2,5], [5,2], [5,5]],
            [[2,3],[2,4],[4,2],[3,2],[3,5],[4,5],[5,3],[5,4]],
            [[0,2],[0,5],[2,0],[5,0],[2,7],[5,7],[7,2],[7,5]],
            [[0,3],[0,4],[3,0],[4,0],[3,7],[4,7],[7,3],[7,4]],
            [[1,2],[1,5],[2,1],[5,1],[2,6],[5,6],[6,2],[6,5]],
            [[1,3],[1,4],[3,2],[4,2],[4,5],[3,5],[6,3],[6,4]],
            [[0,1],[1,0],[0,6],[1,7],[6,0],[7,1],[6,7],[7,6]],
            [[1,1], [1,6], [5,1], [5,6]]
        ]
        temp = turn_positions[random.randrange(0, len(turn_positions))]
        updateBoard(tep_board, tile, temp[0], temp[1])

        # 转换轮次
        if tile == COMPUTER_NUM:
            tile = PLAYER_NUM
        else:
            tile = COMPUTER_NUM

        return find_playout(tep_board, tile, depth=depth + 1)

    def expand(tep_board, tile):
        positions = possible_positions(tep_board, tile)
        result = []
        for temp in positions:
            result.append((temp, 0, 0, []))
        return result

    def find_path(root, total_playout):
        current_path = []
        child = root
        parent_playout = total_playout
        isMCTSTurn = True

        while True:
            if len(child) == 0:
                break
            maxidxlist = [0]
            cidx = 0
            if isMCTSTurn:
                maxval = -1
            else:
                maxval = 2

            for n_tuple in child:
                parent, t_playout, reward, t_childrens = n_tuple

                #实现最大最小搜索，电脑选择最大值，玩家选择最小值
                if isMCTSTurn:
                    cval = ucb1(n_tuple, parent_playout, 0.1)

                    if cval >= maxval:
                        if cval == maxval:
                            maxidxlist.append(cidx)
                        else:
                            maxidxlist = [cidx]
                            maxval = cval
                else:
                    cval = ucb1(n_tuple, parent_playout, -0.1)

                    if cval <= maxval:
                        if cval == maxval:
                            maxidxlist.append(cidx)
                        else:
                            maxidxlist = [cidx]
                            maxval = cval

                cidx += 1

            # 随机进行下棋，扩展
            maxidx = maxidxlist[random.randrange(0, len(maxidxlist))]
            parent, t_playout, reward, t_childrens = child[maxidx]
            current_path.append(parent)
            parent_playout = t_playout
            child = t_childrens
            isMCTSTurn = not (isMCTSTurn)

        return current_path

    root = expand(board, COMPUTER_NUM)
    current_board = getNewBoard()
    current_board2 = getNewBoard()
    start_time = time.time()

    for loop in range(0, 6666):

        # 思考最大时间限制
        if (time.time() - start_time) >= MAX_THINK_TIME:
            ##break
            a=1
        # current_path是一个放置棋子的位置列表，根据此列表进行后续操作
        current_path = find_path(root, loop)

        tile = COMPUTER_NUM
        for temp in current_path:
            updateBoard(current_board, tile, temp[0], temp[1])
            if tile == COMPUTER_NUM:
                tile = PLAYER_NUM
            else:
                tile = COMPUTER_NUM

        #复制棋盘，因为会在find_playout函数修改了棋盘
        isWon = find_playout(current_board2, tile)

        #自顶向下传递参数
        child = root
        for temp in current_path:
            idx = 0
            for n_tuple in child:
                parent, t_playout, reward, t_childrens = n_tuple
                if temp[0] == parent[0] and temp[1] == parent[1]:
                    break
                idx += 1

            if temp[0] == parent[0] and temp[1] == parent[1]:
                t_playout += 1
                if isWon:
                    reward += 1
                if t_playout >= 5 and len(t_childrens) == 0:
                    t_childrens = expand(current_board, tile)

                child[idx] = (parent, t_playout, reward, t_childrens)

            child = t_childrens

    print("loop count: ", loop)
    max_avg_reward = -1
    mt_result = (0,0)
    for n_tuple in root:
        parent, t_playout, reward, t_childrens = n_tuple

        if (t_playout > 0) and (reward / t_playout > max_avg_reward):
            mt_result = parent
            max_avg_reward = reward / t_playout

    return mt_result




# 在棋盘xstart行ystart列方格处放由tile指定黑或白棋子是否符合规则，合规返回需翻转对方棋子，否则返回False
def isValidMove(board, tile, xstart, ystart):       #board是记录棋盘中棋子如何分布的2维列表
    # 如果该位置已经有棋子或者出界了，返回False
    if not isOnBoard(xstart, ystart) or board[xstart][ystart] != 'none':
        return False 
    # 临时将tile 放到指定的位置
    board[xstart][ystart] = tile 
    if tile == 'black':                 #设定本方棋子和对方棋子
        otherTile = 'white'
    else:
        otherTile = 'black'
    # 得到8个方向要被翻转的对方棋子的行列数保存到列表tilesToFlip
    tilesToFlip = []        #下句，如(xdirection,ydirection)=[0, 1],从落子处向右侧查找，即每次列值+1
    for xdirection, ydirection in [ [0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1] ]:
        x, y = xstart, ystart                           #落子处的行列数
        x += xdirection
        y += ydirection
        if isOnBoard(x, y) and board[x][y] == otherTile:  #行列合法值0-7，如果行列数都不出界并且该方格有对方棋子
            x += xdirection                               
            y += ydirection
            if not isOnBoard(x, y):                       #下一位置如出界，此方向没有要翻转的对方棋子，查下一方向
                continue
            # 一直走到出界或不是对方棋子的位置
            while board[x][y] == otherTile:
                x += xdirection
                y += ydirection
                if not isOnBoard(x, y):
                    break
            # 出界了，则没有棋子要翻转OXXXXX       O是己方，X是对方
            if not isOnBoard(x, y):
                continue
            # 是自己的棋子OXXXXXXO              中间的X都要翻转,从最后X开始，逐一向前所有X的行列数都要保存到列表
            if board[x][y] == tile:             #如是己方棋子，说明此方向排列为：OXXXXXXO
                while True:
                    x -= xdirection
                    y -= ydirection
                    # 回到了起点则结束
                    if x == xstart and y == ystart:
                        break
                    # 需要翻转的棋子
                    tilesToFlip.append([x, y])
    # 将前面临时放上的棋子去掉，即还原棋盘
    board[xstart][ystart] = 'none' # restore the empty space
    # 没有要被翻转的棋子，则走法非法。翻转棋的规则。
    if len(tilesToFlip) == 0:   # If no tiles were flipped, this is not a valid move.
        return False
    return tilesToFlip
# 是否出界
def isOnBoard(x, y):
    return x >= 0 and x <= 7 and y >= 0 and y <=7
# 获取可落子的位置
def getValidMoves(board, tile):
    validMoves = []
    for x in range(8):
        for y in range(8):
            if isValidMove(board, tile, x, y) != False:
                validMoves.append([x, y])
    return validMoves

# 将一个tile棋子放到(xstart, ystart)
def makeMove(board, tile, xstart, ystart,p):
    tilesToFlip = isValidMove(board, tile, xstart, ystart)          #得到要翻转的所有对方棋子位置
    print(tilesToFlip)
    if tilesToFlip == False:         #如果列表为空，即无可翻转的对方棋子,放子非法。注意bool([])==False
        return False
    putPiece(board,xstart,ystart,tile,p)            #放棋子
    for x, y in tilesToFlip:                        #翻转对方棋子
        w.delete(allPieces[x,y])                    #删除对方棋子
        putPiece(board,x,y,tile,p)                  #放己方棋子
    if tile==computerTile: #为计算机白棋增加放子标记，+为计算机放的白子，*是被反转的黑子，注意tag都是"A"
        w.create_text((44+xstart*40),(45+ystart*40), text = "+",fill="red",tag="A",font=("Arial",20))
        for x, y in tilesToFlip:
            w.create_text((44+x*40),(45+y*40), text = "*",fill="red",tag="A",font=("Arial",20))
    return True

def showGameEnd(board):
    gameOver=True
    score=getScoreOfBoard(board)                        #得到双方分数，注意返回字典
    if score[computerTile]>score[playerTile]:           #score[computerTile]为计算机得分
        label['text']="游戏结束\n玩家输了"
    elif score[computerTile]<score[playerTile]:         #score[playerTile]为玩家得分
        label['text']="游戏结束\n玩家赢了"
    else:
        label['text']="游戏结束\n平局"

def showScoe(board):                      #显示分数
    score=getScoreOfBoard(board)  #得到双方分数，注意返回字典
 
   ## label1['text']="计算机得分:\n"+str(countTile(board, 'white'))  #score[computerTile]为计算机得分
    ##label2['text']="玩家得分:\n"+str(countTile(board, 'black'))     #score[playerTile]为玩家得分                 
    label1['text']="计算机得分:\n"+str(score[computerTile])  #score[computerTile]为计算机得分
    label2['text']="玩家得分:\n"+str(score[playerTile])      #score[playerTile]为玩家得分         
#玩家用鼠标点击棋盘，启动鼠标点击事件函数，放黑子
def mouseClick(event):                  #event.x,event.y鼠标左键的x,y坐标
    global gameOver,turn
    if turn == 'player' and gameOver==False:
        label['text']=""                #删除前边提示信息
        x,y=(event.x),(event.y) #x,y可能非法包括：该位置有子，无子但不能反转白子，不在方格内
        col = int((x-23)/40)    #23为8*8网格图右边在x轴方向距背景图左边距离
        row = int((y-24)/40)    #24为8*8网格图上边在y轴方向距背景图上边距离,40为方格长和宽
        if makeMove(mainBoard,playerTile,col,row,pb)==False:#放黑子,如位置非法，不能放子
            return                                          #玩家重新放子,提示不变
        showScoe(mainBoard)                                 #到此处玩家已放子，显示分数
        w.delete("A")                                       #到此处玩家已放子，可去掉提示
        if getValidMoves(mainBoard, computerTile) != []:    #返回计算机可放子位置,如有子可放
            turn = 'computer'                               #转计算机放子，游戏一定未结束
            return
        #到此电脑无子可放,如玩家也无子可放,可能已放64子或某方得分为0，或棋子布局使双方都不能放子
        #因此游戏结束，根据得分判断输赢。否则提示：电脑无子可放,玩家放子,然后退出本函数
        if getValidMoves(mainBoard, playerTile) == []:      #返回玩家可放子位置,如无子可放
            showGameEnd(mainBoard)                          #游戏结束
        else:
            label['text']="电脑无子可放\n玩家放子" #到此计算机无子可放，玩家有子可放，提示玩家放子 
            makePlayerMark()        #返回下次玩家可放棋子所有位置

def makePlayerMark():               #返回下次玩家可放棋子所有位置，并为这些位置做标记
    possibleMoves = getValidMoves(mainBoard, playerTile)    #得到玩家可放子所有位置    
    if  possibleMoves!= [] and v.get()==1:                  #如玩家有子可放及复选框"加标记否"选中
        for x, y in possibleMoves:                          #在玩家可放子所有位置做标记
            w.create_text((44+x*40),(45+y*40), text = "~",tag="A",font=("Arial",20))
    return  possibleMoves                                   #返回下次玩家可放棋子所有位置                                              
#收到自定义事件函数，调用本函数，计算机放白子
def computerPlay(event):
    global gameOver,turn   
    if turn == 'computer' and gameOver==False:
        turn='n'#在运行函数computerPlay时，不允许再发事件makeComputerPlay，再次调用computerPlay                               
        ##x, y = getComputerMove(mainBoard, computerTile)         #计算放白子最优位置在(x,y)
        x,y=mctsNextPosition(mainBoard)
        print(x)
        print(y)
        ##updateBoard(mainBoard, COMPUTER_NUM, x, y)
        makeMove(mainBoard, computerTile,x,y,pw)                #计算机放子
        showScoe(mainBoard)                                      #到此处计算机已放子，显示分数
        if makePlayerMark()!= []:#makePlayerMark返回下次玩家可放棋子所有位置，并为这些位置做标记
            turn = 'player'                        #如下次玩家有放棋子的位置，turn = 'player'
            return                                                  
        if getValidMoves(mainBoard, computerTile) == []:       #到此玩家无子可放，如计算机也无子可放
            showGameEnd(mainBoard)                             #游戏结束
        else:                                      #如此玩家无子可放，计算机有子可放，计算机继续放棋子
            label['text']="玩家无子可放\n电脑放子"
            turn = 'computer'         #令turn=='computer'时，允许再发事件makeComputerPlay  

def count():                #该函数完成每秒查看是否轮到计算机放白子功能，将运行在子线程中
    global turn
    while True:
        if turn == 'computer':                              #如轮到计算机放白子
            root.event_generate('<<makeComputerPlay>>')     #发消息启动计算机放白子程序
        time.sleep(1)
def playAgain():
    global w,allPieces,turn,gameOver,playerTile,computerTile,mainBoard,timer
    w.delete("p")#删除所有棋子,见博文"在Python tkinter的Canvas画布上删除所有相同tag属性对象的方法"
    w.delete("A")               #删除所有提醒标志
    allPieces={}                #清空所有棋子的引用ID
    turn = 'player'             #玩家先放棋子
    gameOver = False
    playerTile = 'black'        #玩家使用黑子
    computerTile = 'white'      #计算机使用白子
    label['text']='玩家先放子'
    label1['text']='计算机得分:\n0'
    label2['text']='玩家得分:\n0'
    mainBoard = getNewBoard()   #建立8*8新棋盘,初始值为"none",放2白2黑共棋子，返回ID
    timer=Timer(1, count)       #执行timer.start()语句后，1秒后调用count函数在另一线程运行
    timer.setDaemon(True)       #使主进程结束后子线程也会随之结束。
    timer.start()

root = tk.Tk()                      #初始化窗口
root.title('黑白棋')                 #窗口标题
root.geometry("455x371+200+20") #窗口宽450,高=373,窗口左上点离屏幕左边界200,离屏幕上边界距离20。
root.resizable(width=False,height=False)    #设置窗口是否可变，宽不可变，高不可变，默认为True
w = tk.Canvas(root, width = 372, height = 373, background = "white")        #创建Canvas对象
w.pack(side=tk.LEFT, anchor=tk.NW)                          #放置Canvas对象在root窗体左上角
w.bind("<Button-1>",mouseClick)                             #画布与鼠标左键单击事件绑定
root.bind("<<makeComputerPlay>>",computerPlay) 	  #将自定义事件makeComputerPlay和事件函数绑定
#拷贝所有代码不能运行,必须找到这3个文件,存到运行程序所在文件夹下子文件夹pic中!!!!,也可下载本人程序
pp = tk.PhotoImage(file='黑白棋棋盘.png')       #围棋棋盘图像宽和高为372x373像素
pw = tk.PhotoImage(file='围棋白棋子.png')       #棋子图像必须是png格式，其背景必须是透明的
pb = tk.PhotoImage(file='围棋黑棋子.png')   
w.create_image(0,0, image=pp,anchor = tk.NW)       #放置棋盘图像对象在Canvas对象左上角
label=tk.Label(root,font=("Arial",10))
label.place(x=375,y=2,width=90,height=30)
label1=tk.Label(root,font=("Arial",10),text='计算机得分:0')
label1.place(x=375,y=52,width=80,height=30)
label2=tk.Label(root,font=("Arial",10),text='玩家得分:0')
label2.place(x=375,y=102,width=70,height=30)
button=tk.Button(root,text="重玩游戏", command=playAgain)
button.place(x=379,y=250,width = 70,height = 20)
v = tk.IntVar()
c1=tk.Checkbutton(root,variable = v,text = "加标记否")
c1.place(x=379,y=300,width = 70,height = 30)
v.set(1)        #Checkbutton被设置为选中，将为玩家提示可放棋子位置
playAgain()         #游戏初始化
root.mainloop()	