// Snake game implementation for custom OS
// No stdlib dependency
#include "snake.h"
#include "print_functions.h"
#include "helppers.h"


// Game characters
#define CHAR_EMPTY ' '
#define CHAR_SNAKE 'O'
#define CHAR_HEAD '@'
#define CHAR_FOOD '*'
#define CHAR_WALL '#'

// Game variables
SnakePos snake_body[MAX_SNAKE_LENGTH];
int snake_length;
int direction;
SnakePos food_pos;
int score;
int game_over;
unsigned int tick_counter;
unsigned int seed;
int snake_running = 0;
// void init_snake_keyboard();
//void restore_keyboard_handler();
// Original keyboard handler (saved so we can restore it when game ends)
//void (*original_keyboard_handler)(struct InterruptRegisters *regs) = 0;

// Simple pseudo-random number generator (Linear Congruential Generator)
unsigned int next_random() {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed;
}

// Set a random seed based on current tick count
void init_random(unsigned int initial_seed) {
    seed = initial_seed;
}

// Get a random position within the board boundaries
SnakePos get_random_position() {
    SnakePos pos;
    pos.x = (next_random() % (BOARD_WIDTH - 2)) + 1;
    pos.y = (next_random() % (BOARD_HEIGHT - 2)) + 1;
    return pos;
}

// Check if two positions are the same
int positions_equal(SnakePos a, SnakePos b) {
    return (a.x == b.x && a.y == b.y);
}

// Check if position is part of the snake (except the head)
int is_position_on_snake(SnakePos pos) {
    for (int i = 1; i < snake_length; i++) {
        if (positions_equal(pos, snake_body[i])) {
            return 1;
        }
    }
    return 0;
}

// Generate a new food position
void generate_food() {
    do {
        food_pos = get_random_position();
    } while (is_position_on_snake(food_pos));
}

// Initialize the game
void init_game() {
    // Initialize snake in the middle of the board
    snake_length = 3;
    SnakePos center;
    center.x = BOARD_WIDTH / 2;
    center.y = BOARD_HEIGHT / 2;
    
    // Place snake body parts
    for (int i = 0; i < snake_length; i++) {
        snake_body[i].x = center.x - i;
        snake_body[i].y = center.y;
    }
    
    // Set initial direction
    direction = DIR_RIGHT;
    
    // Initialize score
    score = 0;
    
    // Set game_over flag
    game_over = 0;
    
    // Set tick counter
    tick_counter = 0;
    
    // Initialize random seed
    init_random(42);
    
    // Generate first food
    generate_food();
}

// Draw a character at the specified position
void draw_char_at_position(SnakePos pos, char ch) {
    // Calculate screen offset
    int offset = get_offset(pos.x, pos.y);
    set_char_at(ch, offset);
}

// Draw the game board
void draw_board() {
    // Clear screen
    clear_Screen();
    
    // Draw top and bottom walls
    for (int x = 0; x < BOARD_WIDTH; x++) {
        SnakePos wall_pos;
        wall_pos.x = x;
        
        // Top wall
        wall_pos.y = 0;
        draw_char_at_position(wall_pos, CHAR_WALL);
        
        // Bottom wall
        wall_pos.y = BOARD_HEIGHT - 1;
        draw_char_at_position(wall_pos, CHAR_WALL);
    }
    
    // Draw left and right walls
    for (int y = 0; y < BOARD_HEIGHT; y++) {
        SnakePos wall_pos;
        wall_pos.y = y;
        
        // Left wall
        wall_pos.x = 0;
        draw_char_at_position(wall_pos, CHAR_WALL);
        
        // Right wall
        wall_pos.x = BOARD_WIDTH - 1;
        draw_char_at_position(wall_pos, CHAR_WALL);
    }
    
    // Draw snake
    for (int i = 0; i < snake_length; i++) {
        char ch = (i == 0) ? CHAR_HEAD : CHAR_SNAKE;
        draw_char_at_position(snake_body[i], ch);
    }
    
    // Draw food
    draw_char_at_position(food_pos, CHAR_FOOD);
    
    // Draw score
    SnakePos score_pos;
    score_pos.x = BOARD_WIDTH + 2;
    score_pos.y = 1;
    draw_char_at_position(score_pos, 'S');
    
    score_pos.x++;
    draw_char_at_position(score_pos, 'c');
    
    score_pos.x++;
    draw_char_at_position(score_pos, 'o');
    
    score_pos.x++;
    draw_char_at_position(score_pos, 'r');
    
    score_pos.x++;
    draw_char_at_position(score_pos, 'e');
    
    score_pos.x++;
    draw_char_at_position(score_pos, ':');
    
    score_pos.x++;
    draw_char_at_position(score_pos, ' ');
    
    // Convert score to characters and display
    int temp_score = score;
    if (temp_score == 0) {
        score_pos.x++;
        draw_char_at_position(score_pos, '0');
    } else {
        int digits[10];
        int num_digits = 0;
        
        while (temp_score > 0) {
            digits[num_digits++] = temp_score % 10;
            temp_score /= 10;
        }
        
        for (int i = num_digits - 1; i >= 0; i--) {
            score_pos.x++;
            draw_char_at_position(score_pos, '0' + digits[i]);
        }
    }
    
    // If game over, show message
    if (game_over) {
        SnakePos game_over_pos;
        game_over_pos.x = BOARD_WIDTH / 2 - 4;
        game_over_pos.y = BOARD_HEIGHT / 2;
        
        char* message = "GAME OVER";
        for (int i = 0; message[i] != 0; i++) {
            draw_char_at_position(game_over_pos, message[i]);
            game_over_pos.x++;
        }
        
        game_over_pos.x = BOARD_WIDTH / 2 - 8;
        game_over_pos.y = BOARD_HEIGHT / 2 + 1;
        
        char* restart_msg = "Press R to restart";
        for (int i = 0; restart_msg[i] != 0; i++) {
            draw_char_at_position(game_over_pos, restart_msg[i]);
            game_over_pos.x++;
        }
    }
}

// Process keyboard input to change direction
void process_input() {
    // Direction is directly updated by the keyboard handler
    // We just need to increment the tick counter for game timing
    tick_counter++;
    
    // Note: Our keyboard handler in snake_keyboard.c updates the
    // direction variable directly when arrow keys are pressed
}

// Update the game state
void update_game() {
    if (game_over) {
        // Check if restart was requested (game_over == 2 means restart)
        if (game_over == 2) {
            init_game(); // Restart the game
        }
        return;
    }
   
    // Calculate new head position based on current direction
    SnakePos new_head = snake_body[0];
    
    switch (direction) {
        case DIR_UP:
            new_head.y--;
            break;
        case DIR_RIGHT:
            new_head.x++;
            break;
        case DIR_DOWN:
            new_head.y++;
            break;
        case DIR_LEFT:
            new_head.x--;
            break;
    }
    
    // Check for collisions with walls
    if (new_head.x <= 0 || new_head.x >= BOARD_WIDTH - 1 || 
        new_head.y <= 0 || new_head.y >= BOARD_HEIGHT - 1) {
        game_over = 1;
        return;
    }
    
    // Check for collisions with self
    if (is_position_on_snake(new_head)) {
        game_over = 1;
        return;
    }
    
    // Check for food collision
    int ate_food = positions_equal(new_head, food_pos);
    
    // Move the snake by updating positions
    // First, shift all segments one position down
    for (int i = snake_length - 1; i > 0; i--) {
        snake_body[i] = snake_body[i - 1];
    }
    
    // Set the new head position
    snake_body[0] = new_head;
    
    // If the snake ate food, increase its length and generate new food
    if (ate_food) {
        score++;
        
        if (snake_length < MAX_SNAKE_LENGTH) {
            snake_length++;
        }
        
        generate_food();
    }
}

// Simple delay function using a loop
void delay(unsigned int count) {
    for (unsigned int i = 0; i < count; i++) {
        // Do nothing, just waste time
        for (unsigned int j = 0; j < 1000; j++) {
            // Inner loop to waste more time
        }
    }
}

// Main game loop
void run_snake_game() {
    // Set snake_running flag
    snake_running = 1;
    
    // Initialize the game
    init_game();
    
    // Main game loop
    while (snake_running) {
        
        // Draw the current game state
        draw_board();
        
        // Process input
        //process_input();
       // int a=1/0;
        // Update game state
        //update_game();
        
        // Add a delay to control game speed
        //delay(200000);
    }
    
    // Game has ended, clean up
    // Restore original keyboard handler
   // restore_keyboard_handler();
    
    // Clear screen and print returning to shell message
    clear_Screen();
    print_Str("Snake game ended. Returning to shell.\n");
    print_Str(">");
}

// Function to start the snake game (to be called from shell)
void snake_game() {
    // Clear the screen
    clear_Screen();
    
    // Display welcome message
    print_Str("Welcome to Snake Game!\n");
    print_Str("Use WASD keys to control the snake\n");
    print_Str("* Eat food to grow and increase score\n");
    print_Str("* Avoid hitting walls and yourself\n");
    print_Str("* Press R to restart when game over\n");
    print_Str("* Press Q to quit back to shell\n");
    print_Str("\nPress any key to start...\n");
    
    // Wait for a key press
    delay(200000);
    
    // Save the original keyboard handler and initialize snake keyboard
    
    // Start the game
   //int a=1/0;
    run_snake_game();
}