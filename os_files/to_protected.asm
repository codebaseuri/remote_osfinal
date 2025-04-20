[bits 16]
switch_TO_32:
cli
lgdt [gdt_descriptor]
mov eax , cr0
or eax, 1
mov cr0,eax ; this block changes to 32 bit mode
jmp CODE_SEG:init_32bit; this is far jump

[bits 32]
init_32bit:
mov ax , DATA_SEG
mov ds,ax 
mov es,ax 
mov ss, ax
mov gs, ax 
mov fs,ax

mov ebp , 0x90000
mov esp , ebp; setup the stack 
call BEGIN_32BIT
