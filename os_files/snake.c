

#include "snake.h"
// Custom random function that doesn't rely on stdlib
unsigned int seed = 12345;
Snake snake;
Food food;
char board[HEIGHT][WIDTH];
int score;
int game_over = 0;
int custom_random(int max) {
    // Simple LCG (Linear Congruential Generator)
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return (seed % max);
}

// Initialize the game
void init_game() {
    score = 0;
    game_over = 1;
    // Initialize snake in the middle of the board
    snake.length = 1;
    snake.x[0] = WIDTH / 2;
    snake.y[0] = HEIGHT / 2;
    snake.direction = SRIGHT;

    // Place initial food
    food.x = custom_random(WIDTH - 2) + 1;
    food.y = custom_random(HEIGHT - 2) + 1;
}

// Move the snake based on current direction
void move_snake() {
    int i;
    
    // Move the snake: first shift all segments
    for (i = snake.length - 1; i > 0; i--) {
        snake.x[i] = snake.x[i-1];
        snake.y[i] = snake.y[i-1];
    }
    
    // Move the head according to direction
    switch (snake.direction) {
        case SUP:
            snake.y[0]--;
            break;
        case SRIGHT:
            snake.x[0]++;
            break;
        case SDOWN:
            snake.y[0]++;
            break;
        case SLEFT:
            snake.x[0]--;
            break;
    }
}

// Check for collisions
int check_collision() {
    int i;
    
    // Check for collision with walls
    if (snake.x[0] <= 0 || snake.x[0] >= WIDTH - 1 || 
        snake.y[0] <= 0 || snake.y[0] >= HEIGHT - 1) {
        return 1;
    }
    
    // Check for collision with self
    for (i = 1; i < snake.length; i++) {
        if (snake.x[0] == snake.x[i] && snake.y[0] == snake.y[i]) {
            return 1;
        }
    }
    
    return 0;
}
int continue_game(){return game_over;}
// Check if snake ate food
int check_food() {
    if (snake.x[0] == food.x && snake.y[0] == food.y) {
        // Increase score and length
        score += 10;
        snake.length++;
        
        // Ensure we're not exceeding the snake's array size
        if (snake.length >= 100) {
            char win_msg[] = "You win! The snake can't grow anymore!";
            print_Str(win_msg);
            return 0;
        }
        
        // Generate new food (ensuring it's not on the snake)
        int on_snake;
        do {
            food.x = custom_random(WIDTH - 2) + 1;
            food.y = custom_random(HEIGHT - 2) + 1;
            
            on_snake = 0;
            for (int i = 0; i < snake.length; i++) {
                if (food.x == snake.x[i] && food.y == snake.y[i]) {
                    on_snake = 1;
                    break;
                }
            }
        } while (on_snake);
        
        return 1;
    }
    return 0;
}

// Check for keyboard input and update snake direction
int process_input(char ch ) {
    int moved = 0;
    
    // W key - Up
    if (ch== 'w') {
        if (snake.direction != SDOWN) {
            snake.direction = SUP;
            move_snake();
            moved = 1;
        }
    }
    // A key - Left
    else if (ch== 'a') {
        if (snake.direction != SRIGHT) {
            snake.direction = SLEFT;
            move_snake();
            moved = 1;
        }
    }
    // S key - Down
    else if (ch== 's') {
        if (snake.direction != SUP) {
            snake.direction = SDOWN;
            move_snake();
            moved = 1;
        }
    }
    // D key - Right
    else if (ch== 'd') {
        if (snake.direction != SLEFT) {
            snake.direction = SRIGHT;
            move_snake();
            moved = 1;
        }
    }
    // Q key - Quit
    else if (ch== 'q') {

        clear_Screen();
        print_Str("you quit the game!\n");
        print_Str("returning to shell...\n");
        game_over = 0;
        return 0;
    }
    
    return moved;
}

// Render the game board using your OS's print functions
void render_game() {
    int i, j;
    char buffer[2];  // Buffer for single character printing
    buffer[1] = 0;   // Null terminator
    
    // Clear the board array
    for (i = 0; i < HEIGHT; i++) {
        for (j = 0; j < WIDTH; j++) {
            if (i == 0 || i == HEIGHT - 1 || j == 0 || j == WIDTH - 1)
                board[i][j] = WALL_CHAR;  // Wall
            else
                board[i][j] = EMPTY_SPACE;  // Empty space
        }
    }
    
    // Place food
    board[food.y][food.x] = FOOD_CHAR;
    
    // Place snake
    board[snake.y[0]][snake.x[0]] = SNAKE_HEAD;  // Head
    for (i = 1; i < snake.length; i++) {
        board[snake.y[i]][snake.x[i]] = SNAKE_BODY;  // Body
    }
    
    // Clear screen using your OS function
    clear_Screen();
    
    // Print board using your OS function
    for (i = 0; i < HEIGHT; i++) {
        for (j = 0; j < WIDTH; j++) {
            buffer[0] = board[i][j];
            print_Str(buffer);
        }
        print_Str("\n");
    }
    
    // Print score
    char score_msg[50];
    char score_str[10];
    
    // Convert score to string (simple implementation)
    int temp = score;
    int idx = 0;
    
    // Handle 0 score specially
    if (temp == 0) {
        score_str[idx++] = '0';
    } else {
        // Convert digits in reverse order
        while (temp > 0) {
            score_str[idx++] = '0' + (temp % 10);
            temp /= 10;
        }
    }
    score_str[idx] = '\0';
    
    // Reverse the score string
    for (i = 0; i < idx / 2; i++) {
        char temp = score_str[i];
        score_str[i] = score_str[idx - i - 1];
        score_str[idx - i - 1] = temp;
    }
    
    // Create and print score message
    print_Str("\nScore: ");
    print_Str(score_str);
    print_Str("\n");
    print_Str("Controls: W (up), A (left), S (down), D (right), Q (quit)\n");
    print_Str("Movement: Snake only moves when you press a key\n");
}

// Game loop function - to be called from your main kernel
void run_snake_game() {
    // Initialize game
    init_game();
    
    // Initial render
    render_game();
    

    // Game over message
    clear_Screen();
    print_Str("Welcome to the snake game!\n");
    print_Str("Press 'q' to quit the game.\n");
    print_Str("Press 'w' (up), 'a' (left), 's' (down), 'd' (right) to move.\n");
    print_Str("Press any key to start the game.\n");
    
}