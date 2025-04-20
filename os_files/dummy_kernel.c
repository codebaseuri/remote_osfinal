//___ wlecome to the main kernel.file 
// i have decided to split certain codes into diffrent
// files for readability and cuz im a responsible and 
// and reasonable human being.

// defines for curser functions
#include "print_functions.h"
//initializes the isr,irq i hope 
#include "idt_setup.h"
#include "keybaord.h"
void main() {
    clear_Screen();
    initialize_idt();
    initKeyboard();
    char strr[]="welcome mortals\n";
    print_Str(strr);
    print_Str("made by uri \n");
    print_Str(">");
    
    
}
