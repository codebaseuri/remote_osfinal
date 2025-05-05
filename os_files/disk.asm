

[BITS 16]

disk_load:
pusha
push dx
mov ah, 2
mov al , dh
mov cl , 2 
mov ch,0
mov dh, 0 
int 0x13
jc print_error
jmp returnn


print_error:
    mov si , Messagge
    mov ah, 0x0e

    loppp:
    lodsb 
    cmp al,0
    jz disk_loop
    int 0x10

    jmp loppp
    returnn:
pop dx 
popa
ret


disk_loop:

jmp disk_loop

Messagge db "problem in loading disk please fix it you dummy", 0