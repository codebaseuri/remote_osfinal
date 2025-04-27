#include "keybaord.h"

void snake_game();
char capsOn;
char capsLock;
static char key_buffer[256];
int buffer_index = 0;
int buffer_size = 256;
static char clear[]="clear";
const uint32_t UNKNOWN = 0xFFFFFFFF;
const uint32_t ESC = 0xFFFFFFFF - 1;
const uint32_t CTRL = 0xFFFFFFFF - 2;
const uint32_t LSHFT = 0xFFFFFFFF - 3;
const uint32_t RSHFT = 0xFFFFFFFF - 4;
const uint32_t ALT = 0xFFFFFFFF - 5;
const uint32_t F1 = 0xFFFFFFFF - 6;
const uint32_t F2 = 0xFFFFFFFF - 7;
const uint32_t F3 = 0xFFFFFFFF - 8;
const uint32_t F4 = 0xFFFFFFFF - 9;
const uint32_t F5 = 0xFFFFFFFF - 10;
const uint32_t F6 = 0xFFFFFFFF - 11;
const uint32_t F7 = 0xFFFFFFFF - 12;
const uint32_t F8 = 0xFFFFFFFF - 13;
const uint32_t F9 = 0xFFFFFFFF - 14;
const uint32_t F10 = 0xFFFFFFFF - 15;
const uint32_t F11 = 0xFFFFFFFF - 16;
const uint32_t F12 = 0xFFFFFFFF - 17;
const uint32_t SCRLCK = 0xFFFFFFFF - 18;
const uint32_t HOME = 0xFFFFFFFF - 19;
const uint32_t UP = 0xFFFFFFFF - 20;
const uint32_t LEFT = 0xFFFFFFFF - 21;
const uint32_t RIGHT = 0xFFFFFFFF - 22;
const uint32_t DOWN = 0xFFFFFFFF - 23;
const uint32_t PGUP = 0xFFFFFFFF - 24;
const uint32_t PGDOWN = 0xFFFFFFFF - 25;
const uint32_t END = 0xFFFFFFFF - 26;
const uint32_t INS = 0xFFFFFFFF - 27;
const uint32_t DEL = 0xFFFFFFFF - 28;
const uint32_t CAPS = 0xFFFFFFFF - 29;
const uint32_t NONE = 0xFFFFFFFF - 30;
const uint32_t ALTGR = 0xFFFFFFFF - 31;
const uint32_t NUMLCK = 0xFFFFFFFF - 32;
//this is snake stuff.
// Define key codes that we'll use for snake direction
#define KEY_UP     'w'  // w
#define KEY_LEFT   'a'  // a
#define KEY_DOWN   's'  // s
#define KEY_RIGHT  'd'  // d
#define KEY_RESTART 'r' // r
#define KEY_QUIT    'q' // q
int game_mode = 0; // 0 for shell, 1 for snake game
// External variables from snake.c to update
extern int direction;
extern int game_over;
extern int snake_running;

// Last key pressed (updated by our keyboard handler)
volatile char last_key_pressed = 0;

// Flag to indicate if a key has been pressed
volatile int key_pressed = 0;
//. end of snake stuff

const uint32_t lowercase[128] = {
UNKNOWN,ESC,'1','2','3','4','5','6','7','8',
'9','0','-','=','\b','\t','q','w','e','r',
't','y','u','i','o','p','[',']','\n',CTRL,
'a','s','d','f','g','h','j','k','l',';',
'\'','`',LSHFT,'\\','z','x','c','v','b','n','m',',',
'.','/',RSHFT,'*',ALT,' ',CAPS,F1,F2,F3,F4,F5,F6,F7,F8,F9,F10,NUMLCK,SCRLCK,HOME,UP,PGUP,'-',LEFT,UNKNOWN,RIGHT,
'+',END,DOWN,PGDOWN,INS,DEL,UNKNOWN,UNKNOWN,UNKNOWN,F11,F12,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,
UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,
UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,
UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN
};

const uint32_t uppercase[128] = {
    UNKNOWN,ESC,'!','@','#','$','%','^','&','*','(',')','_','+','\b','\t','Q','W','E','R',
'T','Y','U','I','O','P','{','}','\n',CTRL,'A','S','D','F','G','H','J','K','L',':','"','~',LSHFT,'|','Z','X','C',
'V','B','N','M','<','>','?',RSHFT,'*',ALT,' ',CAPS,F1,F2,F3,F4,F5,F6,F7,F8,F9,F10,NUMLCK,SCRLCK,HOME,UP,PGUP,'-',
LEFT,UNKNOWN,RIGHT,'+',END,DOWN,PGDOWN,INS,DEL,UNKNOWN,UNKNOWN,UNKNOWN,F11,F12,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,
UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,
UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,
UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN
};
void clean_buffer(){
    for (int i = 0; i < buffer_size; i++){
        key_buffer[i] = 0;
    }
    buffer_index = 0;
}

//shell available commands
void commands()
{
    //print_Str(key_buffer);
    if (string_compare(key_buffer,"cls"))
    {
        clear_Screen();
    }
    else if (string_compare(key_buffer,"exit"))
    {
        print_Str("exiting...\n");
        //exit(0);
    }
    else if (string_compare(key_buffer,"help"))
    {
        print_Str("commands:\n");
        print_Str("snake\n");
        print_Str("help\n");
        print_Str("cls\n");
        print_Str("exit\n");
    }
    else if (string_compare(key_buffer,"snake"))
    {
        print_Str("lets play some snake\n");
        game_mode = 1;
       // snake_game();
    }
    else
    {
        print_Str("command not found\n");
    }
    clean_buffer();
    print_Str(">");
    
}

void keyboardHandler( registers_stc *regs){
    char scanCode = port_byte_in(0x60) & 0x7F; //What key is pressed
    char press = port_byte_in(0x60) & 0x80; 
    if (game_mode==0)
    { 
        switch(scanCode){
        case 1:
        case 29:
        case 56:
        case 59:
        case 60:
        case 61:
        case 62:
        case 63:
        case 64:
        case 65:
        case 66:
        case 67:
        case 68:
        case 87:
        case 88:
            break;
        case 42:
            //shift key
            if (press == 0){
                capsOn = 1;
            }else{
                capsOn = 0;
            }
            break;
        case 58:
            if (!capsLock && press == 0){
                capsLock = 1;
            }else if (capsLock && press == 0){
                capsLock = 0;
            }
            break;
        default:
            if (press == 0){

                
                if (capsOn || capsLock){
                   //print_Str(uppercase[scanCode]);
                   //print_Str('c');
                   print_char(uppercase[scanCode]);
                   if (buffer_index<= buffer_size){
                    key_buffer[buffer_index] = uppercase[scanCode];
                    buffer_index++;
                    if (uppercase[scanCode] == '\n'){
                       //print_char('k');
                        key_buffer[buffer_index-1] = '\0';    
                        
                        commands();
                    }
                   
                }

                }
                else{
                     //print_Str(lowercase[scanCode]);
                      //print_Str('c');
                   print_char(lowercase[scanCode]);


                   if (buffer_index<= buffer_size){
                    key_buffer[buffer_index] = lowercase[scanCode];
                    buffer_index++;
                    if (lowercase[scanCode] == '\n'){
                       //print_char('k');
                        key_buffer[buffer_index-1] = '\0';    
                        commands();
                    }
                    
                }
            }
        }   
    }
}
    else 
    {
        print_char('s');
        int a=1/0;
        snake_keyboard_handler(scanCode, press);
    }
}
void snake_keyboard_handler(char scanCode, char pressed) {
    print_char('k');
    if (pressed) {
        char key = 0;
        
        // Convert scan code to ASCII using the keyboard mapping
        if (scanCode < 128) {
            key = lowercase[scanCode];
        }
        
        // Store the key press
        last_key_pressed = key;
        key_pressed = 1;
        
        // Check for game quit key (q)
        if (key == KEY_QUIT) {
            // End the game and return to shell
            snake_running = 0;
            game_over = 1;
            return;
        }
        
        if (!game_over) {
            // Update direction based on key press
            // Don't allow 180-degree turns (e.g., if going right, can't immediately go left)
            if (key == KEY_UP && direction != DIR_DOWN) {
                direction = DIR_UP;
            } else if (key == KEY_RIGHT && direction != DIR_LEFT) {
                direction = DIR_RIGHT;
            } else if (key == KEY_DOWN && direction != DIR_UP) {
                direction = DIR_DOWN;
            } else if (key == KEY_LEFT && direction != DIR_RIGHT) {
                direction = DIR_LEFT;
            }
        } else if (key == KEY_RESTART) {
            // Signal for game restart
            game_over = 2; // Special value to indicate restart requested
        }
    }
}


// Restore the original keyboard handler


// Get the last key that was pressed
char get_last_key() {
    return last_key_pressed;
}

// Check if a key has been pressed since last check
int check_key_pressed() {
    if (key_pressed) {
        key_pressed = 0; // Reset the flag
        return 1;
    }
    return 0;
}

void initKeyboard(){
    capsOn = 0;
    capsLock = 0;
    irq_install(1,&keyboardHandler);
}

    