#ifndef SNAKE_H
#define SNAKE_H
#include "idt_setup.h"

// Forward declare the InterruptRegisters struct
//struct InterruptRegisters;

// Game constants
#define BOARD_WIDTH 40
#define BOARD_HEIGHT 20
#define MAX_SNAKE_LENGTH 100

// Direction constants
#define DIR_UP 0
#define DIR_RIGHT 1
#define DIR_DOWN 2
#define DIR_LEFT 3

// Position structure
typedef struct {
    int x;
    int y;
} SnakePos;

// Function declarations
void snake_game(void);
//void init_snake_keyboard(void);
//void restore_keyboard_handler(void);
//void snake_keyboard_handler( registers_stc*regs);

#endif // SNAKE_H