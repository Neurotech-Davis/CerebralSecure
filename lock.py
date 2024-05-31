import time
from IPython.display import display, HTML

code_file_path = './COMM_Files/code_file.txt'
status_file_path = './COMM_Files/status_file.txt'
action_file_path = './COMM_Files/action_file.txt'
focus_file_path = './COMM_Files/focus_file.txt'

real_password = "abbbaa"

for n in range(6):
    while True: #dont get mad this is how im continuously checking the files every 2 seconds
        with open(status_file_path, 'r') as status_file:
            status = status_file.read().strip()
        
        if status == "prompting":
            with open(status_file_path, 'w') as status_file:
                status_file.write("read")
            
            print(f"Please blink or clench your jaw according to password character {n+1}")
            time.sleep(2) 
            
            with open(focus_file_path, 'r') as focus_file:
                focus = focus_file.read().strip()
            
            if focus == "0":
                print("Error: No action")
                with open(focus_file_path, 'w') as focus_file:
                    focus_file.write("")
            else:
                with open(action_file_path, 'r') as action_file:
                    action = action_file.read().strip()
                
                if action == "0":
                    print("Error: No action")
                    with open(action_file_path, 'w') as action_file:
                        action_file.write("")
                else:
                  #  print("breaking")
                    break

with open(code_file_path, 'r') as code_file:
    code = code_file.read().strip()

if code == real_password:
    with open(status_file_path, 'w') as status_file:
        status_file.write("valid user")
    display(HTML('<div style="width:100%;height:100vh;background-color:green;"></div>'))
else:
    with open(status_file_path, 'w') as status_file:
        status_file.write("invalid user")
    display(HTML('<div style="width:100%;height:100vh;background-color:red;"></div>'))
