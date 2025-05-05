#ifndef KEYBAORD_H
#define KEYBAORD_H

#include "idt_setup.h"
#include "stdint.h"
#include "helppers.h"
#include "print_functions.h"

// Key constants
extern const uint32_t UNKNOWN;
extern const uint32_t ESC;
extern const uint32_t CTRL;
extern const uint32_t LSHFT;
extern const uint32_t RSHFT;
extern const uint32_t ALT;
extern const uint32_t F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12;
extern const uint32_t SCRLCK;
extern const uint32_t HOME;
extern const uint32_t UP;
extern const uint32_t LEFT;
extern const uint32_t RIGHT;
extern const uint32_t DOWN;
extern const uint32_t PGUP;
extern const uint32_t PGDOWN;
extern const uint32_t END;
extern const uint32_t INS;
extern const uint32_t DEL;
extern const uint32_t CAPS;
extern const uint32_t NONE;
extern const uint32_t ALTGR;
extern const uint32_t NUMLCK;

// Keyboard mapping arrays
extern const uint32_t lowercase[128];
extern const uint32_t uppercase[128];

// Keyboard state
extern char capsOn;
extern char capsLock;

// Function declarations
void clean_buffer(void);
void commands(void);
void keyboardHandler(registers_stc *regs);
void initKeyboard(void);
void irq_install(int irq_number, void (*handler)( registers_stc*));
void initTimer(void);
#endif 