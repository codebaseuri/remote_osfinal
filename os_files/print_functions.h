

// VGA control registers and offsets
#define VGA_CTRL_REGISTER 0x3D4
#define VGA_DATA_REGISTER 0x3D5
#define VGA_OFFSET_LOW 0x0F
#define VGA_OFFSET_HIGH 0x0E

// Screen settings and colors
#define VIDEO_ADDRESS 0xB8000
#define MAX_ROWS 25
#define MAX_COLS 80
#define WHITE_ON_BLACK 0x0F

// Define an alias for unsigned
typedef unsigned uns;

// Function prototypes
void set_cursor(int offset);
int get_cursor();
void set_char_at(char character, int offset);
int get_row_offset(int offset);
int get_offset(int col, int row);
void clear_Screen();
int scroll_down_line(int offset);
void print_Str(const char *string);
void print_char(char c);

// External functions (assumed to be defined in 0_helpers.c)
unsigned char port_byte_in(unsigned short port);
void port_byte_out(unsigned short port, unsigned char data);
void memory_copy(char *source, char *dest, int no_bytes);

