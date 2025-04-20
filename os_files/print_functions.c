
#include "helppers.h"
#include "print_functions.h"
#define VGA_CTRL_REGISTER 0x3d4
#define VGA_DATA_REGISTER 0x3d5
#define VGA_OFFSET_LOW 0x0f
#define VGA_OFFSET_HIGH 0x0e
//____________________________
//defines for writing to screen
#define video_address 0xb8000 
#define max_rows 25
#define max_colw 80
#define WHIITE_ON_black 0x0f
int scrl_down_line(int offset);


typedef unsigned uns;
// renaming unsigned cuz im lazy  lol and will make
//more concise


void set_cursor(int offset)
{
    offset/=2;
    port_byte_out(VGA_CTRL_REGISTER,VGA_OFFSET_HIGH);
    port_byte_out(VGA_DATA_REGISTER,(unsigned char) (offset>>8));
    port_byte_out(VGA_CTRL_REGISTER,VGA_OFFSET_LOW);
    port_byte_out(VGA_DATA_REGISTER, (unsigned char) (offset & 0xff));
}

int get_cursor() {
    port_byte_out(VGA_CTRL_REGISTER, VGA_OFFSET_HIGH);
    int offset = port_byte_in(VGA_DATA_REGISTER) << 8;
    port_byte_out(VGA_CTRL_REGISTER, VGA_OFFSET_LOW);
    offset += port_byte_in(VGA_DATA_REGISTER);
    return offset * 2;
}
void set_char_at(char character, int offset)
{
    unsigned char* vid_mem=(char*) video_address;
    vid_mem[offset]=character;
    vid_mem[offset+1]=WHIITE_ON_black;

}
int get_row_offset(int offset)
{
    return offset/(max_colw*2);
}



int get_offset(int col, int row) {
    return 2 * (row * max_colw + col);
}

void clear_Screen()
{
    for (int i=0;i<max_colw*max_colw;i++)
    {
        set_char_at(' ',i*2);
    }
    set_cursor(0);
}

int scrl_down_line(int offset)
{
    memory_copy(
        (char *)(get_offset(0,1)+video_address),
        (char *)(get_offset(0,0)+video_address),
        max_colw * (max_rows-1) * 2);
    for (int i=0;i<max_colw;i++)
    {
        set_char_at(' ',get_offset(i,max_rows-1));
    }
    return offset -max_colw*2;
}
void print_Str(const char *string)
{
 int cursor=get_cursor();
 int i =0;
 while(string[i]!=0)
 {
    if (cursor>=max_colw*max_rows*2)
    {
       cursor= scrl_down_line(cursor);
    }
    if (string[i]=='\n')
        cursor=(get_row_offset(cursor)+1)*max_colw*2;

    else{
        set_char_at(string[i],cursor);
         cursor+=2;
    }
    
    i++; 
   //we need to set the cursor forward so next print call can be done correctly
 }
 set_cursor(cursor);
}
void print_char(char c)
{
    int cursor=get_cursor();
    switch (c)
    {
    case '\b':
        int k=cursor-2;
        set_char_at(' ',k);
        set_cursor(k);
        break;
    case '\n':  
        set_cursor(cursor+2*(MAX_COLS)-cursor%MAX_COLS);
        break;
    default:

    set_char_at(c,cursor);
    set_cursor(cursor+2);
    break;
    }
}