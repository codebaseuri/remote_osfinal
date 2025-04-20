
%macro ISR_noerr_cd 1
    global isr%1
    isr%1:
    cli
    push dword 0
    push dword %1
    jmp isr_common_Code
%endmacro

%macro ISR_err_cd 1
    global isr%1
    isr%1:
    cli
    push byte %1
    jmp isr_common_Code
%endmacro


%macro IRQ 2
    global irq%1
    irq%1:
    cli
    push  dword %1
    push  dword %2
     jmp irq_common_code
%endmacro

;isr macro setup ps yes i know its pretty ugly but no one has a better way so bite me 
ISR_noerr_cd 0
ISR_noerr_cd 1
ISR_noerr_cd 2
ISR_noerr_cd 3
ISR_noerr_cd 4
ISR_noerr_cd 5
ISR_noerr_cd 6
ISR_noerr_cd 7
ISR_err_cd 8
ISR_err_cd 9
ISR_err_cd 10
ISR_err_cd 11
ISR_err_cd 12
ISR_err_cd 13
ISR_err_cd 14
ISR_noerr_cd 15
ISR_noerr_cd 16
ISR_noerr_cd 17
ISR_noerr_cd 18
ISR_noerr_cd 19
ISR_noerr_cd 20
ISR_noerr_cd 21
ISR_noerr_cd 22
ISR_noerr_cd 23
ISR_noerr_cd 24
ISR_noerr_cd 25
ISR_noerr_cd 26
ISR_noerr_cd 27
ISR_noerr_cd 28
ISR_noerr_cd 29
ISR_noerr_cd 30
ISR_noerr_cd 31


ISR_noerr_cd 128 ; for syscalls
ISR_noerr_cd 177 ;for syscalls 

;irq
IRQ 0, 32
IRQ   1,    33
IRQ   2,    34
IRQ   3,    35
IRQ   4,    36
IRQ   5,    37
IRQ   6,    38
IRQ   7,    39
IRQ   8,    40
IRQ   9,    41
IRQ  10,    42
IRQ  11,    43
IRQ  12,    44
IRQ  13,    45
IRQ  14,    46
IRQ  15,    47


;functions written in c 

[extern isr_handler]
[extern irq_handler]
; note to self maybe can be optimised if gs and fs are not used in the project 
isr_common_Code:

pusha 

mov eax, ds
push eax 
mov ax , 0x10

mov ds , ax 
mov es, ax 
mov fs, ax 
mov gs,ax 

push esp
; save stack pointer because c functions gonna use it now 
cli
call isr_handler

pop eax
pop eax

mov ds , ax 
mov es, ax 
mov fs, ax 
mov gs,ax 

;pop registers to previos values 
popa
add esp , 8
sti 
iret 



irq_common_code:
pusha 

mov eax, ds
push eax 
mov ax , 0x10

mov ds , ax 
mov es, ax 
mov fs, ax 
mov gs,ax 

push esp ; save stack pointer because c functions gonna use it now 
call irq_handler

pop eax
pop eax

mov ds , ax 
mov es, ax 
mov fs, ax 
mov gs,ax 

;pop registers to previos values 
popa
add esp , 8 
iret 