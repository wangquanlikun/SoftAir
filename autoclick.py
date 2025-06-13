import pyautogui
import time

minute1, minute2, minute3, minute4, minute5, minute6, minute7, minute8, minute9, minute10, \
minute11, minute12, minute13, minute14, minute15, minute16, minute17, minute18, minute19, minute20,\
minute21, minute22, minute23, minute24, minute25 = [True] * 25

click_position = [
    [
        (32, 124),
        (32, 220),
        (32, 316),
        (32, 412),
        (32, 508)
    ],
    [
        (32, 718),
        (32, 814),
        (32, 910),
        (32, 1006),
        (32, 1102)
    ],
    [
        (890, 124),
        (890, 220),
        (890, 316),
        (890, 412),
        (890, 508)
    ],
    [
        (890, 718),
        (890, 814),
        (890, 910),
        (890, 1006),
        (890, 1102)
    ],
    [
        (1748, 124),
        (1748, 220),
        (1748, 316),
        (1748, 910),
        (1748, 508)
    ]
]
def min0click():
    pyautogui.click(click_position[0][0]) # 1 : On

def min1click():
    print(1)
    pyautogui.click(click_position[0][2])
    pyautogui.click(click_position[0][2])
    pyautogui.click(click_position[0][2])
    pyautogui.click(click_position[0][2])
    pyautogui.click(click_position[0][2])
    pyautogui.click(click_position[0][2])
    pyautogui.click(click_position[0][2]) # 1 : 25 -> 18
    pyautogui.click(click_position[1][0]) # 2 : On
    pyautogui.click(click_position[4][0]) # 5 : On

def min2click():
    print(2)
    pyautogui.click(click_position[2][0]) # 3 : On

def min3click():
    print(3)
    pyautogui.click(click_position[1][2])
    pyautogui.click(click_position[1][2])
    pyautogui.click(click_position[1][2])
    pyautogui.click(click_position[1][2])
    pyautogui.click(click_position[1][2])
    pyautogui.click(click_position[1][2]) # 2 : 25 -> 19
    pyautogui.click(click_position[3][0]) # 4 : On

def min4click():
    print(4)
    pyautogui.click(click_position[4][2])
    pyautogui.click(click_position[4][2])
    pyautogui.click(click_position[4][2]) # 5 : 25 -> 22

def min5click():
    print(5)
    pyautogui.click(click_position[0][4])
    pyautogui.click(click_position[0][0]) # 1 : High

def min6click():
    print(6)
    pyautogui.click(click_position[1][0])
    pyautogui.click(click_position[1][0]) # 2 : Off

def min7click():
    print(7)
    pyautogui.click(click_position[1][0]) # 2 : On
    pyautogui.click(click_position[4][4]) # 5 : High

def min8click():
    print(8)

def min9click():
    print(9)
    pyautogui.click(click_position[0][1])
    pyautogui.click(click_position[0][1])
    pyautogui.click(click_position[0][1])
    pyautogui.click(click_position[0][1]) # 1 : 18 -> 22

    pyautogui.click(click_position[3][2])
    pyautogui.click(click_position[3][2])
    pyautogui.click(click_position[3][2])
    pyautogui.click(click_position[3][2])
    pyautogui.click(click_position[3][2])
    pyautogui.click(click_position[3][2])
    pyautogui.click(click_position[3][2]) # 4 : 25 -> 18
    pyautogui.click(click_position[3][4])
    pyautogui.click(click_position[3][0]) # 4 : High

def min10click():
    print(10)

def min11click():
    print(11)
    pyautogui.click(click_position[1][1])
    pyautogui.click(click_position[1][1])
    pyautogui.click(click_position[1][1]) # 2 : 19 -> 22

def min12click():
    print(12)
    pyautogui.click(click_position[4][4])
    pyautogui.click(click_position[4][0]) # 5 : Low

def min13click():
    print(13)

def min14click():
    print(14)
    pyautogui.click(click_position[0][0]) # 1 : Off
    pyautogui.click(click_position[2][2]) # 3 : 25 -> 24
    pyautogui.click(click_position[2][4])
    pyautogui.click(click_position[2][4]) # 3 : Low

def min15click():
    print(15)
    pyautogui.click(click_position[4][2])
    pyautogui.click(click_position[4][2]) # 5 : 22 -> 20
    pyautogui.click(click_position[4][4])
    pyautogui.click(click_position[4][4])
    pyautogui.click(click_position[4][0]) # 5 : High

def min16click():
    print(16)
    pyautogui.click(click_position[1][0]) # 2 : Off

def min17click():
    print(17)
    pyautogui.click(click_position[2][4])
    pyautogui.click(click_position[2][4]) # 3 : High

def min18click():
    print(18)
    pyautogui.click(click_position[0][0]) # 1 : On
    pyautogui.click(click_position[3][1])
    pyautogui.click(click_position[3][1]) # 4 : 18 -> 20
    pyautogui.click(click_position[3][4])
    pyautogui.click(click_position[3][4]) # 4: Middle

def min19click():
    print(19)
    pyautogui.click(click_position[1][0]) # 2 : On

def min20click():
    print(20)
    pyautogui.click(click_position[4][1])
    pyautogui.click(click_position[4][1])
    pyautogui.click(click_position[4][1])
    pyautogui.click(click_position[4][1])
    pyautogui.click(click_position[4][1]) # 5 : 20 -> 25

def min21click():
    print(21)

def min22click():
    print(22)
    pyautogui.click(click_position[2][0])
    pyautogui.click(click_position[2][0]) # 3 : Off

def min23click():
    print(23)
    pyautogui.click(click_position[4][0]) # 5 : Off

def min24click():
    print(24)
    pyautogui.click(click_position[0][0]) # 1 : Off

def min25click():
    print(25)
    pyautogui.click(click_position[1][0]) # 2 : Off
    pyautogui.click(click_position[3][0]) # 4 : Off

if __name__ == "__main__":
    startTime = time.time()
    min0click()

    while True:
        now = time.time()
        minute = int((now - startTime) // 10.2) # 假设每10.2秒钟点击一次
        
        if minute == 1 and minute1:
            min1click()
            pyautogui.click(1748, 910)
            minute1 = False
        elif minute == 2 and minute2:
            min2click()
            pyautogui.click(1748, 910)
            minute2 = False
        elif minute == 3 and minute3:
            min3click()
            pyautogui.click(1748, 910)
            minute3 = False
        elif minute == 4 and minute4:
            min4click()
            pyautogui.click(1748, 910)
            minute4 = False
        elif minute == 5 and minute5:
            min5click()
            pyautogui.click(1748, 910)
            minute5 = False
        elif minute == 6 and minute6:
            min6click()
            pyautogui.click(1748, 910)
            minute6 = False
        elif minute == 7 and minute7:
            min7click()
            pyautogui.click(1748, 910)
            minute7 = False
        elif minute == 8 and minute8:
            min8click()
            pyautogui.click(1748, 910)
            minute8 = False
        elif minute == 9 and minute9:
            min9click()
            pyautogui.click(1748, 910)
            minute9 = False
        elif minute == 10 and minute10:
            min10click()
            pyautogui.click(1748, 910)
            minute10 = False
        elif minute == 11 and minute11:
            min11click()
            pyautogui.click(1748, 910)
            minute11 = False
        elif minute == 12 and minute12:
            min12click()
            pyautogui.click(1748, 910)
            minute12 = False
        elif minute == 13 and minute13:
            min13click()
            pyautogui.click(1748, 910)
            minute13 = False
        elif minute == 14 and minute14:
            min14click()
            pyautogui.click(1748, 910)
            minute14 = False
        elif minute == 15 and minute15:
            min15click()
            pyautogui.click(1748, 910)
            minute15 = False
        elif minute == 16 and minute16:
            min16click()
            pyautogui.click(1748, 910)
            minute16 = False
        elif minute == 17 and minute17:
            min17click()
            pyautogui.click(1748, 910)
            minute17 = False
        elif minute == 18 and minute18:
            min18click()
            pyautogui.click(1748, 910)
            minute18 = False
        elif minute == 19 and minute19:
            min19click()
            pyautogui.click(1748, 910)
            minute19 = False
        elif minute == 20 and minute20:
            min20click()
            pyautogui.click(1748, 910)
            minute20 = False
        elif minute == 21 and minute21:
            min21click()
            pyautogui.click(1748, 910)
            minute21 = False
        elif minute == 22 and minute22:
            min22click()
            pyautogui.click(1748, 910)
            minute22 = False
        elif minute == 23 and minute23:
            min23click()
            pyautogui.click(1748, 910)
            minute23 = False
        elif minute == 24 and minute24:
            min24click()
            pyautogui.click(1748, 910)
            minute24 = False
        elif minute == 25 and minute25:
            min25click()
            pyautogui.click(1748, 910)
            minute25 = False
            break

        time.sleep(0.01)  # 每0.01秒检查一次

    print("Finished clicking all minutes.")