#ifndef SNAKE_H
#define SNAKE_H

// Game board dimensions
#define WIDTH 30
#define HEIGHT 15  // Reduced to fit better on screen

// Direction constants
#define SUP 0
#define SRIGHT 1
#define SDOWN 2
#define SLEFT 3

// Game characters
#define WALL_CHAR '#'
#define SNAKE_HEAD 'O'
#define SNAKE_BODY 'o'
#define FOOD_CHAR '@'
#define EMPTY_SPACE ' '

// Key controls
#define KEY_UP 'w'      // w
#define KEY_LEFT 'a'    // a
#define KEY_DOWN 's'    // s
#define KEY_RIGHT 'd'   // d
#define KEY_RESTART 'r' // r
#define KEY_QUIT 'q'    // q

// Snake structure
typedef struct {
    int x[100];  // X coordinates of snake segments
    int y[100];  // Y coordinates of snake segments
    int length;  // Current length of the snake
    int direction;  // Current direction
} Snake;

// Food structure
typedef struct {
    int x;
    int y;
} Food;

// Game state variables (extern so keyboard.c can access them)


// Function declarations
int custom_random(int max);
void init_game();
void move_snake();
int check_collision();
int check_food();
int process_input(char ch);
void render_game();
void run_snake_game();
int continue_game();

#endif /* SNAKE_H */
