
from picrawler import Picrawler
from time import sleep
import readchar

crawler = Picrawler([10,11,12,4,5,6,1,2,3,7,8,9]) 
speed = 90

manual = '''
Press keys on keyboard to control PiCrawler!
    w: Forward
    a: Turn left
    s: Backward
    d: Turn right
    esc: Quit
'''

def show_info():
    print("\033[H\033[J",end='')  # clear terminal windows 
    print(manual)


def main(): 
    show_info()   
    while True:
        key = readchar.readkey()
        key = key.lower()
        if key in('wsad'):
            if 'w' == key:
                crawler.do_action('forward',1,speed)     
            elif 's' == key:
                crawler.do_action('backward',1,speed)          
            elif 'a' == key:
                crawler.do_action('turn left',1,speed)           
            elif 'd' == key:
                crawler.do_action('turn right',1,speed)
            sleep(0.05)
            show_info()  
        elif key == readchar.key.CTRL_C or key in readchar.key.ESCAPE_SEQUENCES:
            print("\n Quit") 
            break    
        
        sleep(0.02)          
     
 
if __name__ == "__main__":
    main()