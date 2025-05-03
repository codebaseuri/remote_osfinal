#include "keybaord.h"
#include "snake.h"

char capsOn;
char capsLock;
static char key_buffer[256];
int buffer_index = 0;
int buffer_size = 256;
int is_snake = 0;
int game_mode = 0;
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


// Flag to indicate if a key has been pressed
volatile int key_pressed = 0;
//. end of snake stuff

const uint32_t lowercase[128] = {
    UNKNOWN, ESC,     '1',     '2',     '3',     '4',     '5',     '6',
    '7',     '8',     '9',     '0',     '-',     '=',     '\b',    '\t',
    'q',     'w',     'e',     'r',     't',     'y',     'u',     'i',
    'o',     'p',     '[',     ']',     '\n',    CTRL,    'a',     's',
    'd',     'f',     'g',     'h',     'j',     'k',     'l',     ';',
    '\'',    '`',     LSHFT,   '\\',    'z',     'x',     'c',     'v',
    'b',     'n',     'm',     ',',     '.',     '/',     RSHFT,   '*',
    ALT,     ' ',     CAPS,    F1,      F2,      F3,      F4,      F5,
    F6,      F7,      F8,      F9,      F10,     NUMLCK,  SCRLCK,  HOME,
    UP,      PGUP,    '-',     LEFT,    UNKNOWN, RIGHT,   '+',     END,
    DOWN,    PGDOWN,  INS,     DEL,     UNKNOWN, UNKNOWN, UNKNOWN, F11,
    F12,     UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN,
    UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN,
    UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN,
    UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN,
    UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN};

const uint32_t uppercase[128] = {
    UNKNOWN, ESC,     '!',     '@',     '#',     '$',     '%',     '^',
    '&',     '*',     '(',     ')',     '_',     '+',     '\b',    '\t',
    'Q',     'W',     'E',     'R',     'T',     'Y',     'U',     'I',
    'O',     'P',     '{',     '}',     '\n',    CTRL,    'A',     'S',
    'D',     'F',     'G',     'H',     'J',     'K',     'L',     ':',
    '"',     '~',     LSHFT,   '|',     'Z',     'X',     'C',     'V',
    'B',     'N',     'M',     '<',     '>',     '?',     RSHFT,   '*',
    ALT,     ' ',     CAPS,    F1,      F2,      F3,      F4,      F5,
    F6,      F7,      F8,      F9,      F10,     NUMLCK,  SCRLCK,  HOME,
    UP,      PGUP,    '-',     LEFT,    UNKNOWN, RIGHT,   '+',     END,
    DOWN,    PGDOWN,  INS,     DEL,     UNKNOWN, UNKNOWN, UNKNOWN, F11,
    F12,     UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN,
    UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN,
    UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN,
    UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN,
    UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN};
void clean_buffer() {
  for (int i = 0; i < buffer_size; i++) {
    key_buffer[i] = 0;
  }
  buffer_index = 0;
}

// shell available commands
void commands() {
  // print_Str(key_buffer);
  if (string_compare(key_buffer, "cls")) {
    clear_Screen();
  } else if (string_compare(key_buffer, "exit")) {
    print_Str("exiting...\n");
    // exit(0);
  } else if (string_compare(key_buffer, "help")) {
    print_Str("commands:\n");
    print_Str("snake\n");
    print_Str("help\n");
    print_Str("cls\n");
    print_Str("exit\n");
  } else if (string_compare(key_buffer, "snake")) {
    print_Str("Runinng snake");
    print_Str("lets play some snake\n");

    game_mode = 1;
    is_snake = 1;
    run_snake_game();
  } else {
    print_Str("command not found\n");
  }
  clean_buffer();
  print_Str(">");
}
char get_char(unsigned char scanCode) {
  if(scanCode > sizeof(lowercase) / sizeof(lowercase[0])) {
    return '\0';
  }
  return lowercase[scanCode];
}

void shell_handler(char scanCode , char press){
    
    switch(scanCode){
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
                print_char(uppercase[scanCode]);
                if (buffer_index<= buffer_size){
                key_buffer[buffer_index] = uppercase[scanCode];
                buffer_index++;
                if (uppercase[scanCode] == '\n'){
                    key_buffer[buffer_index-1] = '\0';    
                    
                    commands();
                }
                
            }

            }
            else{
                print_char(lowercase[scanCode]);


                if (buffer_index<= buffer_size){
                key_buffer[buffer_index] = lowercase[scanCode];
                buffer_index++;
                if (lowercase[scanCode] == '\n'){
                    key_buffer[buffer_index-1] = '\0';    
                    commands();
                }
                
            }
        }
    }   
}
}



void snake_keyboard_handler_ch(char ch){

 
    
    if (process_input(ch)==1) {
        // If the snake moved, check for collisions
        if (check_collision()) {
            is_snake = 0;
            // Clear the screen and print game over message
            print_Str("Game Over!");
        } else {
            // Check if food was eaten
            check_food();
            
            // Re-render the game
            render_game();
        }
    }
        else if (continue_game() == 0)
        {
            is_snake = 0;
            delay(100);
            print_Str("Game Over! you quit the game!\n");
            delay(50);
            print_Str("cleaning up now \n");
            delay(100);
            clear_Screen();
            print_Str(">");
        }
}

void keyboardHandler(registers_stc *regs){
  char scanCode = port_byte_in(0x60); // & 0x7F; // What key is pressed
  char press = port_byte_in(0x60) & 0x80;
  char ch = get_char(scanCode);
  if(ch == '\0'){
    return;
  }
  if(is_snake){

    snake_keyboard_handler_ch(ch);
    return;
  }
  shell_handler(scanCode, press);
}


// Get the last key that was pressed
// Check if a key has been pressed since last check
int check_key_pressed() {
  if (key_pressed) {
    key_pressed = 0; // Reset the flag
    return 1;
  }
  return 0;
}

void initKeyboard() {
  capsOn = 0;
  capsLock = 0;
  irq_install(1, &keyboardHandler);
}
